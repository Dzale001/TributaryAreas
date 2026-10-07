import re

testo = """Selezionare oggetti:
                  LWPOLYLINE  Layer: "aree"
                            Spazio: Spazio modello
                     Gestore = 194ed
            Aperta
larghezza costante    0.0000
              area   1125.7039
         lunghezza   142.5439
          al punto  X=3570.8396  Y=1404.3062  Z=   0.0000
          al punto  X=3575.8396  Y=1399.3062  Z=   0.0000
          al punto  X=3598.8896  Y=1399.3062  Z=   0.0000
          al punto  X=3598.8896  Y=1359.6198  Z=   0.0000
          al punto  X=3570.8396  Y=1359.6198  Z=   0.0000
          al punto  X=3570.8396  Y=1404.3062  Z=   0.0000
                  LWPOLYLINE  Layer: "aree"
                            Spazio: Spazio modello
                     Gestore = 194f7
            Chiusa
larghezza costante    0.0000
              area   1477.8306
         perimetro   155.5248
Premere INVIO per continuare:
          al punto  X=3639.5235  Y=1363.2813  Z=   0.0000
          al punto  X=3598.8896  Y=1363.2813  Z=   0.0000
          al punto  X=3598.8896  Y=1399.3062  Z=   0.0000
          al punto  X=3621.9396  Y=1399.3062  Z=   0.0000
          al punto  X=3624.9396  Y=1402.1062  Z=   0.0000
          al punto  X=3626.9396  Y=1402.1062  Z=   0.0000
          al punto  X=3629.9396  Y=1399.3062  Z=   0.0000
          al punto  X=3639.5235  Y=1399.3062  Z=   0.0000
          al punto  X=3639.5235  Y=1367.6139  Z=   0.0000
                  LWPOLYLINE  Layer: "aree"
                            Spazio: Spazio modello
                     Gestore = 194f6
            Chiusa
larghezza costante    0.0000
              area   1245.4529
         perimetro   250.3940
          al punto  X=3653.1396  Y=1300.0062  Z=   0.0000
          al punto  X=3648.1396  Y=1305.0062  Z=   0.0000
          al punto  X=3639.0896  Y=1305.0062  Z=   0.0000
          al punto  X=3639.0896  Y=1345.7062  Z=   0.0000
Premere INVIO per continuare:
          al punto  X=3648.1396  Y=1345.7062  Z=   0.0000
          al punto  X=3650.9396  Y=1348.5062  Z=   0.0000
          al punto  X=3650.9396  Y=1350.7062  Z=   0.0000
          al punto  X=3648.1396  Y=1353.5062  Z=   0.0000
          al punto  X=3639.5235  Y=1353.5062  Z=   0.0000
          al punto  X=3639.5235  Y=1399.3062  Z=   0.0000
          al punto  X=3648.1396  Y=1399.3062  Z=   0.0000
          al punto  X=3653.1396  Y=1404.3062  Z=   0.0000
                  LWPOLYLINE  Layer: "aree"
                            Spazio: Spazio modello
                     Gestore = 194ef
            Chiusa
larghezza costante    0.0000
              area   862.4442
         perimetro   117.5933
          al punto  X=3570.8396  Y=1359.6198  Z=   0.0000
          al punto  X=3598.8896  Y=1359.6198  Z=   0.0000
          al punto  X=3598.8896  Y=1328.8731  Z=   0.0000
          al punto  X=3570.8396  Y=1328.8731  Z=   0.0000
                  LWPOLYLINE  Layer: "aree"
Premere INVIO per continuare:
                            Spazio: Spazio modello
                     Gestore = 194f0
            Chiusa
larghezza costante    0.0000
              area   463.1778
         perimetro   95.3050
          al punto  X=3570.8396  Y=1307.8062  Z=   0.0000
          al punto  X=3570.8396  Y=1328.8731  Z=   0.0000
          al punto  X=3598.8896  Y=1328.8731  Z=   0.0000
          al punto  X=3598.8896  Y=1312.8062  Z=   0.0000
          al punto  X=3575.8396  Y=1312.8062  Z=   0.0000
                  LWPOLYLINE  Layer: "aree"
                            Spazio: Spazio modello
                     Gestore = 195c4
            Chiusa
larghezza costante    0.0000
              area   1214.4774
         perimetro   147.8069
          al punto  X=3598.8896  Y=1342.5942  Z=   0.0000
          al punto  X=3639.0896  Y=1342.5942  Z=   0.0000
          al punto  X=3639.0896  Y=1312.8062  Z=   0.0000
Premere INVIO per continuare:
          al punto  X=3629.9396  Y=1312.8062  Z=   0.0000
          al punto  X=3626.9396  Y=1307.8062  Z=   0.0000
          al punto  X=3625.0396  Y=1307.8062  Z=   0.0000
          al punto  X=3625.0396  Y=1312.8062  Z=   0.0000
          al punto  X=3598.8896  Y=1312.8062  Z=   0.0000
                  LWPOLYLINE  Layer: "aree"
                            Spazio: Spazio modello
                     Gestore = 194f4
            Chiusa
larghezza costante    0.0000
              area   114.9100
         perimetro   51.9713
          al punto  X=3623.1396  Y=1300.0062  Z=   0.0000
          al punto  X=3623.1396  Y=1307.8062  Z=   0.0000
          al punto  X=3626.9396  Y=1307.8062  Z=   0.0000
          al punto  X=3629.9396  Y=1312.8062  Z=   0.0000
          al punto  X=3639.0896  Y=1312.8062  Z=   0.0000
          al punto  X=3639.0896  Y=1305.0062  Z=   0.0000
          al punto  X=3629.9396  Y=1305.0062  Z=   0.0000

"""




pattern = re.compile(r"area\s+([\d]+\.?[\d]*)")
aree = pattern.findall(testo)

# --- Conversione a interi ---
# Opzione A: ARROTONDAMENTO (consigliata)
aree_interi = [round(float(a)) for a in aree]

# Opzione B: TRONCAMENTO (decommenta se preferisci)
# aree_interi = [int(float(a)) for a in aree]

# --- Output per Excel ---
print("Aree trovate:", len(aree_interi))
print()

# Colonna (una per riga)
print("=== Da incollare in colonna ===")
print("\n".join(str(a) for a in aree_interi))

# Riga singola (separata da tab)
print()
print("=== Da incollare in riga ===")
print("\t".join(str(a) for a in aree_interi))

# Salva su file
with open("aree.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(str(a) for a in aree_interi))

print()
print("Salvato: aree.txt")