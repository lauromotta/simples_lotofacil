"""
ETL - Extract, Transform, Load para dados da Lotofácil.

Importa dados históricos da API e carrega no banco de dados.
Calcula estatísticas automaticamente.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
import requests
import hashlib
import json
from sqlalchemy.orm import Session

from app.io.database import Database, Draw, DrawStats, get_database
from app.core.combinatorics import (
    soma_jogo,
    contar_pares_impares,
    maior_sequencia_consecutiva,
    distribuicao_quadrantes,
)


class LotofacilETL:
    """
    ETL para dados da Lotofácil.

    Extrai dados da API, transforma e carrega no banco.
    """

    def __init__(
        self,
        api_url: str = "https://loteriascaixa-api.herokuapp.com/api/lotofacil",
        database: Optional[Database] = None
    ):
        """
        Inicializa ETL.

        Args:
            api_url: URL da API da Lotofácil
            database: Instância de Database (cria se None)
        """
        self.api_url = api_url
        self.database = database or get_database()

    def extract(self, timeout: int = 30) -> List[Dict]:
        """
        Extrai dados da API.

        Args:
            timeout: Timeout em segundos

        Returns:
            Lista de dicionários com dados dos sorteios

        Raises:
            requests.exceptions.RequestException: Erro na requisição
        """
        print(f"🌐 Extraindo dados da API: {self.api_url}")

        response = requests.get(self.api_url, timeout=timeout)
        response.raise_for_status()

        dados = response.json()
        print(f"✓ {len(dados)} sorteios extraídos")

        return dados

    def transform(self, raw_data: List[Dict]) -> Tuple[List[Draw], List[DrawStats]]:
        """
        Transforma dados brutos em models.

        Args:
            raw_data: Dados brutos da API

        Returns:
            Tupla (lista de Draws, lista de DrawStats)
        """
        print(f"🔄 Transformando {len(raw_data)} sorteios...")

        draws = []
        stats = []

        for item in raw_data:
            # Extrair dados básicos
            concurso = item.get("concurso")
            data = item.get("data", "")
            dezenas = [int(n) for n in item.get("dezenas", [])]

            if not concurso or len(dezenas) != 15:
                print(f"  ⚠️  Concurso {concurso} inválido, pulando...")
                continue

            # Valor arrecadado
            valor_arrecadado = item.get("valorArrecadado", 0.0)

            # Ganhadores com 15 acertos
            ganhadores_15 = 0
            for premiacao in item.get("premiacoes", []):
                if premiacao.get("descricao") == "15 acertos" or premiacao.get("faixa") == 1:
                    ganhadores_15 = premiacao.get("ganhadores", 0)
                    break

            # Criar Draw
            draw = Draw(
                concurso=concurso,
                data=data,
                nums_15=dezenas,
                valor_arrecadado=valor_arrecadado,
                ganhadores_15=ganhadores_15
            )
            draws.append(draw)

            # Calcular estatísticas
            soma = soma_jogo(dezenas)
            pares, impares = contar_pares_impares(dezenas)
            max_consec = maior_sequencia_consecutiva(dezenas)
            quads = distribuicao_quadrantes(dezenas)

            # Criar DrawStats
            stat = DrawStats(
                concurso=concurso,
                soma=soma,
                pares=pares,
                impares=impares,
                max_consecutivos=max_consec,
                q1=quads["q1"],
                q2=quads["q2"],
                q3=quads["q3"],
                q4=quads["q4"],
                repetidos_anterior=0  # Será calculado depois
            )
            stats.append(stat)

        # Calcular repetições do anterior
        for i in range(1, len(draws)):
            nums_atual = set(draws[i].nums_15)
            nums_anterior = set(draws[i-1].nums_15)
            repeticoes = len(nums_atual & nums_anterior)
            stats[i].repetidos_anterior = repeticoes

        print(f"✓ Transformação concluída")
        return draws, stats

    def load(
        self,
        draws: List[Draw],
        stats: List[DrawStats],
        update_existing: bool = False
    ) -> Dict[str, int]:
        """
        Carrega dados no banco.

        Args:
            draws: Lista de Draws
            stats: Lista de DrawStats
            update_existing: Se True, atualiza registros existentes

        Returns:
            Dicionário com contadores (inserted, updated, skipped)
        """
        print(f"💾 Carregando {len(draws)} sorteios no banco...")

        session = self.database.get_session()
        counters = {"inserted": 0, "updated": 0, "skipped": 0}

        try:
            for draw, stat in zip(draws, stats):
                # Verificar se já existe
                existing = session.query(Draw).filter_by(concurso=draw.concurso).first()

                if existing:
                    if update_existing:
                        # Atualizar
                        existing.data = draw.data
                        existing.nums_15 = draw.nums_15
                        existing.valor_arrecadado = draw.valor_arrecadado
                        existing.ganhadores_15 = draw.ganhadores_15

                        # Atualizar stats
                        existing_stat = session.query(DrawStats).filter_by(
                            concurso=draw.concurso
                        ).first()
                        if existing_stat:
                            existing_stat.soma = stat.soma
                            existing_stat.pares = stat.pares
                            existing_stat.impares = stat.impares
                            existing_stat.max_consecutivos = stat.max_consecutivos
                            existing_stat.q1 = stat.q1
                            existing_stat.q2 = stat.q2
                            existing_stat.q3 = stat.q3
                            existing_stat.q4 = stat.q4
                            existing_stat.repetidos_anterior = stat.repetidos_anterior

                        counters["updated"] += 1
                    else:
                        counters["skipped"] += 1
                else:
                    # Inserir novo
                    session.add(draw)
                    session.flush()  # Para obter o ID

                    session.add(stat)
                    counters["inserted"] += 1

            session.commit()
            print(f"✓ Carga concluída: {counters}")

        except Exception as e:
            session.rollback()
            print(f"❌ Erro na carga: {e}")
            raise
        finally:
            session.close()

        return counters

    def run(
        self,
        timeout: int = 30,
        update_existing: bool = False
    ) -> Dict[str, any]:
        """
        Executa ETL completo (Extract -> Transform -> Load).

        Args:
            timeout: Timeout da API
            update_existing: Se True, atualiza registros existentes

        Returns:
            Dicionário com métricas da execução
        """
        print("=" * 70)
        print("ETL - Lotofácil")
        print("=" * 70)

        start_time = datetime.now()

        try:
            # Extract
            raw_data = self.extract(timeout=timeout)

            # Transform
            draws, stats = self.transform(raw_data)

            # Calcular hash do dataset (antes do load)
            dataset_hash = hashlib.sha256(
                json.dumps([d.concurso for d in draws]).encode()
            ).hexdigest()[:16]

            # Load
            counters = self.load(draws, stats, update_existing=update_existing)

            end_time = datetime.now()
            elapsed = (end_time - start_time).total_seconds()

            result = {
                "success": True,
                "total_draws": len(draws),
                "inserted": counters["inserted"],
                "updated": counters["updated"],
                "skipped": counters["skipped"],
                "dataset_hash": dataset_hash,
                "elapsed_seconds": elapsed,
                "timestamp": end_time.isoformat()
            }

            print(f"\n✅ ETL concluído em {elapsed:.2f}s")
            print(f"   Dataset hash: {dataset_hash}")
            return result

        except Exception as e:
            print(f"\n❌ ETL falhou: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def import_historical_data(
    database_url: Optional[str] = None,
    update_existing: bool = False
) -> Dict[str, any]:
    """
    Função auxiliar para importar dados históricos.

    Args:
        database_url: URL do banco (usa padrão se None)
        update_existing: Se True, atualiza registros existentes

    Returns:
        Dicionário com resultado da execução
    """
    db = get_database(database_url)
    etl = LotofacilETL(database=db)
    return etl.run(update_existing=update_existing)


def get_latest_draw(database_url: Optional[str] = None) -> Optional[Draw]:
    """
    Retorna o último sorteio no banco.

    Args:
        database_url: URL do banco

    Returns:
        Último Draw ou None
    """
    db = get_database(database_url)
    session = db.get_session()

    try:
        draw = session.query(Draw).order_by(Draw.concurso.desc()).first()
        return draw
    finally:
        session.close()


def get_draw_by_concurso(
    concurso: int,
    database_url: Optional[str] = None
) -> Optional[Draw]:
    """
    Busca sorteio por número do concurso.

    Args:
        concurso: Número do concurso
        database_url: URL do banco

    Returns:
        Draw ou None
    """
    db = get_database(database_url)
    session = db.get_session()

    try:
        draw = session.query(Draw).filter_by(concurso=concurso).first()
        return draw
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 70)
    print("TESTE - ETL Lotofácil")
    print("=" * 70)

    # Inicializar banco
    db = get_database("sqlite:///test_etl_lotofacil.db")
    db.create_tables()

    # Executar ETL
    etl = LotofacilETL(database=db)
    result = etl.run()

    # Exibir resultado
    print("\n📊 Resultado do ETL:")
    print(f"   Sucesso: {result['success']}")
    print(f"   Total: {result.get('total_draws', 0)}")
    print(f"   Inseridos: {result.get('inserted', 0)}")
    print(f"   Atualizados: {result.get('updated', 0)}")
    print(f"   Pulados: {result.get('skipped', 0)}")
    print(f"   Tempo: {result.get('elapsed_seconds', 0):.2f}s")

    # Verificar último sorteio
    print("\n🎲 Último sorteio no banco:")
    latest = get_latest_draw("sqlite:///test_etl_lotofacil.db")
    if latest:
        print(f"   Concurso: {latest.concurso}")
        print(f"   Data: {latest.data}")
        print(f"   Números: {latest.nums_15}")

        # Buscar estatísticas
        session = db.get_session()
        stats = session.query(DrawStats).filter_by(concurso=latest.concurso).first()
        if stats:
            print(f"   Soma: {stats.soma}")
            print(f"   Pares: {stats.pares}, Ímpares: {stats.impares}")
            print(f"   Q1: {stats.q1}, Q2: {stats.q2}, Q3: {stats.q3}, Q4: {stats.q4}")
        session.close()

    print("\n" + "=" * 70)
