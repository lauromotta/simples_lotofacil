
import numpy as np
from itertools import permutations
import requests
import pandas as pd
import time
import os
import random
from halo import Halo
import math
import sys

print(sys.version_info)




def dash(d):
    try:
        sys.stdout.write('\r%s' % '                                                                               ')
        sys.stdout.flush()
        sys.stdout.write('\r%s' % d)
        sys.stdout.flush()
    except:
        pass

def downloadURL():
    spinner = Halo(text=f'\nCarregando todos os Jogos', spinner='dots')
    spinner.start()

    html_content = r'http://loterias.caixa.gov.br/wps/portal/loterias/landing/lotofacil/!ut/p/a1/04_Sj9CPykssy0xPLMnMz0vMAfGjzOLNDH0MPAzcDbz8vTxNDRy9_Y2NQ13CDA0sTIEKIoEKnN0dPUzMfQwMDEwsjAw8XZw8XMwtfQ0MPM2I02-AAzgaENIfrh-FqsQ9wBmoxN_FydLAGAgNTKEK8DkRrACPGwpyQyMMMj0VAcySpRM!/dl5/d5/L2dBISEvZ0FBIS9nQSEh/pw/Z7_HGK818G0K85260Q5OIRSC42046/res/id=historicoHTML/c=cacheLevelPage/=/'
    r = requests.get(html_content)
    df_full = pd.read_html(r.text)[0]
    spinner.stop()
    return df_full

def valorTotal(qntJogos, numJogos):
    return len(qntJogos) * 2.5 if numJogos == 15 else len(qntJogos) * 40.0 if numJogos == 16 else len(qntJogos) * 340.0 if numJogos == 17 else len(qntJogos) * 2040.0 if numJogos == 18 else len(qntJogos) * 9690.00 if numJogos == 19 else len(qntJogos) * 38760.0 if numJogos == 20 else 0

def gerarCombincoes(nj=15, adJ=[]):
    if len(adJ) != 0:
        a = set(adJ)
    else:
        a = {}
    while True:
        n = random.randint(1, 25)
        if len(a) == 0:
            a = {n}
        a.add(n)
        if len(a) == nj:
            break
    return list(a)

def minSequencias(seqLista, minSq=3):
    ns = 0
    numSequencia = ns
    b = 0
    for x in seqLista:
        try:
            z = x+1 == seqLista[b+1]
            # print(z, x+1, '==', seqLista[b+1])
            b += 1
            if z:
                numSequencia += 1 
                if numSequencia >= minSq:
                    return False
            else:
                numSequencia = ns
        except:
            continue
    return True

def checkRepeticoeList(qntsJogos, ng):
    geradoNum = np.array(ng)

    adN = 0
    for qtJapends in qntsJogos:
        
        if qtJapends != []:
            geradoListNum = np.array(qtJapends)
            
            # print((geradoNum != geradoListNum).all())
            if (geradoNum == geradoListNum).all():
                return False
                adN += 0
            else:
                adN += 1
        else:
            # print('Error')
            return True
            adN += 0
    return True
    # return True if adN == 0 else False

def qntSequencia(numList):
    lis = numList
    seq = range(1,26) #[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]

    b = []
    for x in seq:
        if x in lis:
            b.append(x)
        else:
            b.append(0)
    so = 0
    t = []
    for d in b:

        if d != 0:
            so += 1

        else:
            if so != 1 and so != 0:
                t.append(so)
            so = 0

    return t

def extends(e):
   
    u = []
    for d in e:
        u.extend(qntSequencia(d))
    return u

def ckSeqJogos(tabela_jogo_Ganhadores):
    tabJogoGa = [list(tjg) for tjg in tabela_jogo_Ganhadores.values]

    ape = []
    for bi in tabJogoGa:
        if bi[15] > 1:
            bi.pop(len(bi)-1)
            ape.append(bi)

    return extends(ape)
    # return ape

def cr(t, c):
    x = {'r': 31,
         'g': 32,  'y': 33,  'b': 34,  'w': 37,  're': 0,  'br': 41,  'bg': 42,  'bb': 44,  'by': 43}
    return '\x1b[' + str(x[c]) + 'm' + str(t) + '\x1b[0m'


def nub(nj):
    if nj == 15:
        return 2
    elif nj >= 16 and nj <= 18:
        return 3
    else:
        return 4



def main():

    qntsJogos = []
    nJogosFeitos = 0

    

    while True:
        try:
            print('Ex. 15 ou 16 ou 17 ou 18 ou 19 ou 20')
            nj = int(input('Número de Jogos: '))#15
            if nj >= 15 and nj <=20:
                break
            else:
                print('Os números tem que esta entre 15 a 20:')
            
        except:
            pass

    minSquencia = list(range(nub(nj), 6))

    while True:
        # print('Ex. 1, 2, 3, 4 ... ou deixe em branco')
        adJ_ = input('Ex. 1, 2, 3, 4 ... ou deixe em branco\nNúmero Manual: ').split(',') #[] # [2,3,8] colocar os numeros manualmente
        if adJ_ != '0' and adJ_ != '':
            try:
                adJ = [int(x) for x in adJ_]
                break
            except:
                adJ = []
                break
        else:
            adJ = []
            break

    combTotal = math.comb(25, nj)
    coT = f'{combTotal:,.3f}'

    while True:
        dash(f'Minimo de combinações {cr(1, "g")} e máximo de {cr(coT[:-4].replace(",", "."), "g")}\nQnt de Jogos a ser feito: ')
        # dash(f'Minimo de combinações {cr(1, "g")} e máximo de {cr(combTotal, "g")}.\nQnt de Jogos a ser feito: ')
        try:
            quatidadesdejogos = int(input())#973
            if quatidadesdejogos <= combTotal and quatidadesdejogos >= 1:
                break
            pass
        except:
            pass

    porc = 100 / quatidadesdejogos
    downl = time.time() - 100

    os.system('cls')

    print(
        f'Total de 25 de {nj} combinações: {cr(coT[:-4].replace(",", "."), "g")}\n')

    while True:

        arr = porc * nJogosFeitos
        
        if downl < time.time():
            
            df_full = downloadURL()
            tabela_jogo = df_full[['Bola1', 'Bola2', 'Bola3', 'Bola4', 'Bola5', 'Bola6', 'Bola7', 'Bola8', 'Bola9', 'Bola10', 'Bola11', 'Bola12', 'Bola13', 'Bola14', 'Bola15']]
            tabela_jogo_Ganhadores = df_full[['Bola1', 'Bola2', 'Bola3', 'Bola4', 'Bola5', 'Bola6', 'Bola7', 'Bola8', 'Bola9', 'Bola10', 'Bola11', 'Bola12', 'Bola13', 'Bola14', 'Bola15', 'Ganhadores_15_N��meros']]
            tabelaJogos = [list(ix) for ix in tabela_jogo.values]
            downl = time.time() + 3600
        
        
        nJogosFeitos += 1

        if len(qntsJogos) == quatidadesdejogos:
            time.sleep(2)
            # spinner.stop()
            break
        
        
        js = random.choice(minSquencia)
        inicioTime = time.time() + 300
        ne = 0
        
        while True:

            ng = gerarCombincoes(nj=nj, adJ=adJ)  # Gerar os numeros
            ms = minSequencias(list(ng), js)  # maximo de sequencias dos numeros

            bol = checkRepeticoeList(qntsJogos, ng) # Checar repetição de jogos
            
            if nj == 15:
                bolTodosJogos = checkRepeticoeList(tabelaJogos, ng) # checar se já saiu o jogo
            else:
                bolTodosJogos = True
                
            if  time.time() > inicioTime:
                js += 1
                ne += 1
                if ne == 0:
                    inicioTime = time.time() + 240
                elif ne == 1:
                    inicioTime = time.time() + 180
                else:
                    inicioTime = time.time() + 120
                
            itenRan = ['🤑', '🍀', ' ☘', '🙏', '🙇']

            grn = f" ".ljust(4)+            f"✅ Sequências Analisadas: ".ljust(18) + f"{' - '.join(map(str, [cr(str(xi).zfill(2), 'g') for xi in ng]))} | ({str(nJogosFeitos).zfill(2)}) {random.choice(itenRan)}                           \n"
            rd =  f"{int(arr)}% ".ljust(4)+ f"❌ Analisando Sequências: ".ljust(18) + f"{' - '.join(map(str, [cr(str(xi).zfill(2), 'r') for xi in ng]))} | ({str(nJogosFeitos).zfill(2)}) {str(round(inicioTime - time.time(), 2)).zfill(3)}s"

            
            dash(grn if ms == True and bolTodosJogos  == True and bol == True else rd)
            time.sleep(0.1)


            if ms and bolTodosJogos and bol:
                break

        qntsJogos.append(ng)

        
    vTotal = f'R$ {valorTotal(qntsJogos, nj):_.2f}'
    vTotal = vTotal.replace('.', ",").replace('_', '.')
    print(f'\nValor Total dos {len(qntsJogos)} jogos: {cr(vTotal, "g")}')


if __name__ == '__main__':
    main()
