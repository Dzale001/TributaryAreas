"""
Azioni climatiche secondo NTC 2018: neve (par. 3.4) e vento (par. 3.3).

Logica ricavata dai fogli Excel "calcolo-azione-neve-ntc18" e
"calcolo-azione-vento-ntc18" (Ing. Davide Cicchini).

Il modulo e' indipendente dall'interfaccia: contiene
  - VOCI_CLIMATICHE : le voci da aggiungere a DATABASE
  - calcola_neve()  / calcola_vento() : funzioni di calcolo pure
"""
import math

# =====================================================================
# NEVE  (par. 3.4 NTC18)
# =====================================================================

# zona: (qsk per as <= 200 m [kN/m2], a, b)  ->  qsk = a * (1 + (as/b)^2) per as > 200 m
ZONE_NEVE = {
    "Zona I - Alpina": (1.50, 1.39, 728),
    "Zona I - Mediterranea": (1.50, 1.35, 602),
    "Zona II": (1.00, 0.85, 481),
    "Zona III": (0.60, 0.51, 481),
}

PROVINCE_NEVE = {
    "Zona I - Alpina":
        "Aosta, Belluno, Bergamo, Biella, Bolzano, Brescia, Como, Cuneo, Lecco, "
        "Pordenone, Sondrio, Torino, Trento, Udine, Verbano-Cusio-Ossola, Vercelli, Vicenza",
    "Zona I - Mediterranea":
        "Alessandria, Ancona, Asti, Bologna, Cremona, Forli-Cesena, Lodi, Milano, Modena, "
        "Monza Brianza, Novara, Parma, Pavia, Pesaro e Urbino, Piacenza, Ravenna, "
        "Reggio Emilia, Rimini, Treviso, Varese",
    "Zona II":
        "Arezzo, Ascoli Piceno, Avellino, Bari, Barletta-Andria-Trani, Benevento, Campobasso, "
        "Chieti, Fermo, Ferrara, Firenze, Foggia, Frosinone, Genova, Gorizia, Imperia, Isernia, "
        "L'Aquila, La Spezia, Lucca, Macerata, Mantova, Massa Carrara, Padova, Perugia, Pescara, "
        "Pistoia, Prato, Rieti, Rovigo, Savona, Teramo, Trieste, Venezia, Verona",
    "Zona III":
        "Agrigento, Brindisi, Cagliari, Caltanissetta, Carbonia-Iglesias, Caserta, Catania, "
        "Catanzaro, Cosenza, Crotone, Enna, Grosseto, Latina, Lecce, Livorno, Matera, "
        "Medio Campidano, Messina, Napoli, Nuoro, Ogliastra, Olbia-Tempio, Oristano, Palermo, "
        "Pisa, Potenza, Ragusa, Reggio Calabria, Roma, Salerno, Sassari, Siena, Siracusa, "
        "Taranto, Terni, Trapani, Vibo Valentia, Viterbo",
}

# coefficiente di esposizione CE
CLASSI_TOPOGRAFIA = {
    "Battuta dai venti": 0.9,
    "Normale": 1.0,
    "Riparata": 1.1,
}


def qsk_neve(quota, zona):
    """Carico neve al suolo [kN/m2]."""
    q0, a, b = ZONE_NEVE[zona]
    return q0 if quota <= 200 else a * (1 + (quota / b) ** 2)


def mu1(alfa):
    """Coefficiente di forma mu1 (neve depositata)."""
    if alfa <= 30:
        return 0.8
    if alfa < 60:
        return 0.8 * (60 - alfa) / 30
    return 0.0


def mu2(alfa):
    """Coefficiente di forma mu2 (accumulo in valle, coperture a piu' falde)."""
    if alfa <= 30:
        return 0.8 + 0.8 * alfa / 30
    if alfa < 60:
        return 1.6
    return 0.0


def calcola_neve(p, voce):
    """
    p    : dict con quota, zona, topografia, ct, alfa1, alfa2, barriera(bool)
    voce : dict del database (forma, falda, fattore)
    ritorna dict(valore [kN/m2], dimensioni, info)
    """
    if p["quota"] < 0:
        raise ValueError("L'altitudine as non puo' essere negativa.")

    q_sk = qsk_neve(p["quota"], p["zona"])
    ce = CLASSI_TOPOGRAFIA[p["topografia"]]
    ct = p["ct"]

    if voce["forma"] == "mu1":
        n = voce["falda"]
        alfa = p["alfa1"] if n == 1 else p["alfa2"]
        mu = mu1(alfa)
        if p["barriera"]:
            mu = max(mu, 0.8)       # parapetto/barriera: mu non inferiore a 0,8
        sigla = f"μ1(α{n}={alfa:g}°)"
    else:
        alfa = (p["alfa1"] + p["alfa2"]) / 2
        mu = mu2(alfa)
        sigla = f"μ2(α={alfa:g}°)"

    fattore = voce.get("fattore", 1.0)
    mu_eff = mu * fattore
    qs = mu_eff * q_sk * ce * ct

    if fattore != 1.0:
        sigla = f"{fattore:g}·{sigla}"

    righe = [
        f"qsk = {q_sk:.3f} kN/m²   CE = {ce:g}   Ct = {ct:g}",
        f"{sigla} = {mu_eff:.3f}   →   qs = μ·qsk·CE·Ct = {qs:.3f} kN/m²",
    ]
    if p["quota"] > 1500:
        righe.append("⚠ as > 1500 m: servono valori statistici locali "
                     "(non inferiori a quelli per 1500 m).")

    return {
        "valore": qs,
        "dimensioni": f"as {p['quota']:g} m, {p['zona']}, {sigla}={mu_eff:.2f}",
        "info": "\n".join(righe),
    }


# =====================================================================
# VENTO  (par. 3.3 NTC18)
# =====================================================================

# zona: (vb,0 [m/s], a0 [m], ks)
ZONE_VENTO = {
    "1) Valle d'Aosta, Piemonte, Lombardia, Trentino A.A., Veneto, Friuli V.G. "
    "(eccetto provincia di Trieste)": (25, 1000, 0.40),
    "2) Emilia Romagna": (25, 750, 0.45),
    "3) Toscana, Marche, Umbria, Lazio, Abruzzo, Molise, Puglia, Campania, "
    "Basilicata, Calabria (esclusa provincia di Reggio Calabria)": (27, 500, 0.37),
    "4) Sicilia e provincia di Reggio Calabria": (28, 500, 0.36),
    "5) Sardegna (a oriente della retta Capo Teulada - Isola di Maddalena)": (28, 750, 0.40),
    "6) Sardegna (a occidente della retta Capo Teulada - Isola di Maddalena)": (28, 500, 0.36),
    "7) Liguria": (28, 1000, 0.54),
    "8) Provincia di Trieste": (30, 1500, 0.50),
    "9) Isole (eccetto Sicilia e Sardegna) e mare aperto": (31, 500, 0.32),
}

RUGOSITA = {
    "A": "A) Aree urbane con almeno il 15% della superficie coperta da edifici "
         "di altezza media > 15 m",
    "B": "B) Aree urbane (non di classe A), suburbane, industriali e boschive",
    "C": "C) Aree con ostacoli diffusi (alberi, case, muri, recinzioni...); "
         "aree non riconducibili alle classi A, B, D",
    "D": "D) Aree prive di ostacoli (aperta campagna, aeroporti, aree agricole, "
         "pascoli, zone paludose o sabbiose, superfici innevate o ghiacciate, mare, laghi)",
}

# categoria di esposizione: (kr, z0 [m], zmin [m])
CATEGORIE_ESPOSIZIONE = {
    "I": (0.17, 0.01, 2),
    "II": (0.19, 0.05, 4),
    "III": (0.20, 0.10, 5),
    "IV": (0.22, 0.30, 8),
    "V": (0.23, 0.70, 12),
}

# Tabelle categoria di esposizione (colonne come nel foglio Excel).
# Zone 1-5, colonne: mare | costa<=10 km | <=30 km | >30 km: as<500 | <750 | >=750
# None = combinazione non ammessa.
_T_ZONA_1 = {
    "A": [None, "IV", "IV", "V", "V", "V"],
    "B": [None, "III", "III", "IV", "IV", "IV"],
    "C": [None, "II", "III", "III", "IV", "IV"],
    "D": ["I", "II", "II", "II", "III", "IV"],
}
_T_ZONA_234 = {
    "A": [None, "IV", "IV", "V", "V", "V"],
    "B": [None, "III", "III", "IV", "IV", "IV"],
    "C": [None, "II", "III", "III", "IV", "IV"],
    "D": ["I", "II", "II", "II", "III", "III"],
}
_T_ZONA_5 = {
    "A": [None, "IV", "IV", "V", "V", "V"],
    "B": [None, "III", "III", "IV", "IV", "IV"],
    "C": [None, "III", "III", "III", "IV", "IV"],
    "D": ["I", "II", "II", "II", "III", "III"],
}
# Zona 6, colonne: mare | <=10 km | <=30 km | >30 km: as<500 | as>=500
_T_ZONA_6 = {
    "A": [None, "III", "IV", "V", "V"],
    "B": [None, "II", "III", "IV", "IV"],
    "C": [None, "II", "III", "III", "IV"],
    "D": ["I", "I", "II", "II", "III"],
}
# Zone 7 e 8, colonne: mare oltre 0,5 km | mare entro 0,5 km | terraferma
_T_ZONA_7 = {
    "A": [None, None, "IV"], "B": [None, None, "IV"],
    "C": [None, None, "III"], "D": ["I", "II", "III"],
}
_T_ZONA_8 = {
    "A": [None, None, "IV"], "B": [None, None, "IV"],
    "C": [None, None, "III"], "D": ["I", "II", "II"],
}
# Zona 9, colonne: mare | costa
_T_ZONA_9 = {
    "A": [None, "I"], "B": [None, "I"], "C": [None, "I"], "D": ["I", "I"],
}


def categoria_esposizione(zona, classe, distanza_costa, quota):
    """
    distanza_costa [km]: positiva sulla terraferma, NEGATIVA se in mare
    (come nel foglio Excel). Ritorna 'I'...'V'.
    """
    if distanza_costa < 0:
        classe = "D"            # in mare la classe di rugosita' e' D

    if zona in (1, 2, 3, 4, 5):
        tab = {1: _T_ZONA_1, 2: _T_ZONA_234, 3: _T_ZONA_234,
               4: _T_ZONA_234, 5: _T_ZONA_5}[zona]
        if distanza_costa < 0:
            i = 0
        elif distanza_costa <= 10:
            i = 1
        elif distanza_costa <= 30:
            i = 2
        elif quota < 500:
            i = 3
        elif quota < 750:
            i = 4
        else:
            i = 5
    elif zona == 6:
        tab = _T_ZONA_6
        if distanza_costa < 0:
            i = 0
        elif distanza_costa <= 10:
            i = 1
        elif distanza_costa <= 30:
            i = 2
        else:
            i = 3 if quota < 500 else 4
    elif zona in (7, 8):
        tab = _T_ZONA_7 if zona == 7 else _T_ZONA_8
        if distanza_costa < 0:
            i = 1 if distanza_costa >= -0.5 else 0
        else:
            i = 2
    else:
        tab = _T_ZONA_9
        i = 0 if distanza_costa < 0 else 1

    cat = tab[classe][i]
    if cat is None:
        raise ValueError("Combinazione zona / classe di rugosita' / distanza dalla "
                         "costa non prevista dalla norma.")
    return cat


TOPOGRAFIE = [
    "Condizione non isolata (ct = 1)",
    "Cresta di una collina isolata",
    "Livello superiore di un altopiano isolato",
    "Pendio isolato",
]


def ct_topografico(caso, H, D, h, x, z):
    """Coefficiente topografico (par. 3.3.7), come nel foglio Excel. z = quota di gronda."""
    if caso == TOPOGRAFIE[0]:
        return 1.0
    if H <= 0 or D <= 0 or h <= 0:
        raise ValueError("H, D e h del rilievo devono essere maggiori di zero.")
    s = z / H
    beta = 0.5 if s <= 0.75 else (0.8 - 0.4 * s if s <= 2 else 0.0)
    hd = H / D
    gamma = 0.0 if hd <= 0.1 else (5 * (hd - 0.1) if hd <= 0.3 else 1.0)
    if caso == TOPOGRAFIE[1]:
        return 1 + beta * gamma
    if caso == TOPOGRAFIE[2]:
        return max(1.0, 1 + beta * gamma * (1 - 0.1 * x / h))
    return 1 + beta * gamma * h / H


TIPOLOGIE_VENTO = [
    "Costruzioni completamente stagne",
    "Costruzioni con (o che possono avere) una parete con aperture < 1/3 del totale",
    "Costruzioni con una parete con aperture >= 1/3 del totale",
    "Costruzioni con due pareti opposte, normali al vento, con aperture >= 1/3",
    "Coperture multiple",
    "Tettoia ad uno spiovente",
    "Tettoia a due spioventi",
]
# cpi per ciascuna tipologia: (configurazione A [cpi > 0], configurazione B [cpi < 0])
_CPI = [(0.0, 0.0), (0.2, -0.2), (0.8, -0.5), (0.4, -0.4), (0.2, -0.2), (0.0, 0.0), (0.0, 0.0)]
_IDX_TETTOIA_1 = 5
_IDX_TETTOIA_2 = 6

CONFIGURAZIONI_VENTO = ["Configurazione A (cpi positivo)",
                        "Configurazione B (cpi negativo)",
                        "Piu' sfavorevole (max in valore assoluto)"]

COPERTURE_MULTIPLE = ["Prima copertura investita", "Seconda copertura", "Coperture successive"]
# riduzione 25%: (spiovente sopravento, spiovente sottovento)
_RIDUZIONE_MULTIPLE = [(1.0, 1.0), (0.75, 1.0), (0.75, 0.75)]

SUPERFICI = {"Liscia (acciaio, cls a faccia liscia...)": 0.01,
             "Scabra": 0.02,
             "Molto scabra (ondulata, costolata, piegata...)": 0.04}


def _cp(tip, conf, alfa):
    """cp netti (cpe - cpi) di: parete sopravento, copertura sopravento,
    copertura sottovento, parete sottovento. conf = 'A' o 'B'."""
    tettoia1 = tip == _IDX_TETTOIA_1
    tettoia2 = tip == _IDX_TETTOIA_2
    tettoia = tettoia1 or tettoia2

    if tettoia2:
        cpe_sop = 0.8 * (1 + math.sin(math.radians(alfa)))
    elif tettoia1:
        cpe_sop = 1.2 * (1 + math.sin(math.radians(alfa)))
    elif alfa <= 20:
        cpe_sop = -0.4
    elif alfa >= 60:
        cpe_sop = 0.8
    else:
        cpe_sop = 0.03 * alfa - 1

    if conf == "A":
        cpi = _CPI[tip][0]
        par_sop = 0.0 if tettoia else 0.8 - cpi
        cop_sop = cpe_sop - cpi
        par_sott = 0.0 if tettoia else -0.4 - cpi
        cop_sott = -0.6 if tettoia2 else (0.0 if tettoia1 else -0.4 - cpi)
    else:
        cpi = abs(_CPI[tip][1])
        par_sop = 0.0 if tettoia else 0.8 + cpi
        cop_sop = (-cpe_sop if tettoia else cpe_sop) + cpi
        par_sott = 0.0 if tettoia else -0.4 + cpi
        cop_sott = -0.6 if tettoia2 else (0.0 if tettoia1 else -0.4 + cpi)

    return [par_sop, cop_sop, cop_sott, par_sott]


def calcola_vento(p, voce):
    """
    p : dict con zona, rugosita, quota, distanza, TR, cd, topografia, H, D, h, x,
        tipologia (indice), config (indice), h_colmo, h_gronda, alfa,
        copertura_multipla (indice), superficie
    voce : dict del database (elemento, valore)
    ritorna dict(valore [kN/m2, + verso la superficie, - depressione], dimensioni, info)
    """
    # ---- velocita' e pressione cinetica di riferimento ----
    zona = int(p["zona"][0])
    vb0, a0, ks = ZONE_VENTO[p["zona"]]
    quota = p["quota"]
    if quota < 0:
        raise ValueError("L'altitudine as non puo' essere negativa.")
    ca = 1.0 if quota <= a0 else 1 + ks * (quota / a0 - 1)
    vb = vb0 * ca
    TR = p["TR"]
    if TR <= 1:
        raise ValueError("Il tempo di ritorno deve essere maggiore di 1 anno.")
    cr = 0.75 * math.sqrt(1 - 0.2 * math.log(-math.log(1 - 1 / TR)))
    vr = vb * cr
    qr = 0.5 * 1.25 * vr ** 2            # [N/m2]

    # ---- geometria ----
    zg = p["h_gronda"]
    zc = p["h_colmo"]
    if zc <= 0:
        raise ValueError("L'altezza di colmo deve essere maggiore di zero.")
    if zc < zg:
        raise ValueError("L'altezza di colmo non puo' essere minore di quella di gronda.")
    piana = abs(zc - zg) < 1e-9
    alfa = 2.0 if piana else p["alfa"]      # copertura piana: alfa = 2 gradi (come l'Excel)

    # ---- coefficiente di esposizione ----
    cat = categoria_esposizione(zona, p["rugosita"], p["distanza"], quota)
    kr, z0, zmin = CATEGORIE_ESPOSIZIONE[cat]
    ct = ct_topografico(p["topografia"], p["H"], p["D"], p["h"], p["x"], zg)

    def ce(z):
        z = max(z, zmin)
        ln = math.log(z / z0)
        return kr ** 2 * ct * ln * (7 + ct * ln)

    def ce_medio(a, b, n=400):
        if b - a < 1e-9:
            return ce(b)
        dz = (b - a) / n
        tot = sum((ce(a + i * dz) + ce(a + (i + 1) * dz)) / 2 * dz for i in range(n))
        return tot / (b - a)

    ce_g, ce_c = ce(zg), ce(zc)
    cd = p["cd"]
    tip = p["tipologia"]

    # ---- pressione tangenziale (par. 3.3.5) ----
    if voce["elemento"] == "tangenziale":
        cf = SUPERFICI[p["superficie"]]
        val = qr * ce_c * cf / 1000
        return {
            "valore": val,
            "dimensioni": f"superficie {p['superficie'].split(' ')[0].lower()}, cf={cf:g}",
            "info": (f"qr = {qr:.1f} N/m²   ce(colmo) = {ce_c:.3f}   cf = {cf:g}\n"
                     f"qtan = qr·ce·cf = {val:.4f} kN/m²"),
        }

    # ---- coefficienti di forma ----
    cpA = _cp(tip, "A", alfa)
    cpB = _cp(tip, "B", alfa)
    if p["config"] == 0:
        cp = cpA
    elif p["config"] == 1:
        cp = cpB
    else:
        cp = [a if abs(a) >= abs(b) else b for a, b in zip(cpA, cpB)]

    if tip == 4:        # coperture multiple: riduzione 25%
        r_sop, r_sott = _RIDUZIONE_MULTIPLE[p["copertura_multipla"]]
        cp[1] *= r_sop
        cp[2] *= r_sott

    elementi = {
        "parete_sop": (0, 0.0, zg, "parete sopravento"),
        "copertura_sop": (1, zg, zc, "copertura sopravento"),
        "copertura_sott": (2, zg, zc, "copertura sottovento"),
        "parete_sott": (3, 0.0, zg, "parete sottovento"),
    }
    k, a, b, nome = elementi[voce["elemento"]]
    cp_el = cp[k]

    if voce["valore"] == "max":
        ce_el = ce_g if k in (0, 3) else ce_c
        tipo_val = "pressione massima"
    else:
        ce_el = ce_medio(a, b) if not (k in (1, 2) and piana) else ce_c
        tipo_val = "pressione media"

    val = qr / 1000 * cd * ce_el * cp_el

    conf_txt = ["A", "B", "piu' sfavorevole"][p["config"]]
    righe = [
        f"zona {zona}: vb,0 = {vb0} m/s, ca = {ca:.3f}, vb = {vb:.2f} m/s   cr = {cr:.4f}   "
        f"vr = {vr:.2f} m/s   qr = {qr:.1f} N/m²",
        f"categoria di esposizione {cat} (kr = {kr}, z0 = {z0} m, zmin = {zmin} m)   "
        f"ct = {ct:.3f}   cd = {cd:g}",
        f"ce(gronda) = {ce_g:.3f}   ce(colmo) = {ce_c:.3f}   ce usato ({tipo_val}) = {ce_el:.3f}",
        f"cp {nome} = {cp_el:+.3f} (conf. {conf_txt})   →   "
        f"p = qr·cd·ce·cp = {val:+.4f} kN/m²",
    ]
    if piana:
        righe.append("Copertura piana: α = 2° come nel foglio Excel.")
    if quota > 1500:
        righe.append("⚠ as > 1500 m: verificare la validita' dei parametri di zona.")

    return {
        "valore": val,
        "dimensioni": f"{nome}, {tipo_val}, cp={cp_el:+.2f}, ce={ce_el:.2f}",
        "info": "\n".join(righe),
    }


# =====================================================================
# VOCI PER IL DATABASE
# =====================================================================
_FONTE_NEVE = "NTC 2018 par. 3.4 - calcolo come foglio 'Calcolo azione neve NTC18'"
_FONTE_VENTO = "NTC 2018 par. 3.3 - calcolo come foglio 'Calcolo azione vento NTC18'"


def _neve(forma, falda, fattore=1.0, schema="due"):
    return {"metodo": "neve", "forma": forma, "falda": falda,
            "fattore": fattore, "schema": schema, "fonte": _FONTE_NEVE}


def _vento(elemento, valore="max"):
    return {"metodo": "vento", "elemento": elemento, "valore": valore,
            "fonte": _FONTE_VENTO}


VOCI_CLIMATICHE = {
    "Neve": {
        "NTC 2018 - par. 3.4": {
            "Copertura ad una falda": {
                "Falda (μ1 di α1)": _neve("mu1", 1, schema="una"),
            },
            "Copertura a due falde": {
                "Caso I (neve senza vento) - falda 1 (μ1 α1)": _neve("mu1", 1),
                "Caso I (neve senza vento) - falda 2 (μ1 α2)": _neve("mu1", 2),
                "Caso II (neve con vento) - falda 1 (0,5·μ1 α1)": _neve("mu1", 1, 0.5),
                "Caso II (neve con vento) - falda 2 (μ1 α2)": _neve("mu1", 2),
                "Caso III (neve con vento) - falda 1 (μ1 α1)": _neve("mu1", 1),
                "Caso III (neve con vento) - falda 2 (0,5·μ1 α2)": _neve("mu1", 2, 0.5),
            },
            "Copertura a più falde": {
                "Caso I (neve senza vento) - falda 1 (μ1 α1)": _neve("mu1", 1),
                "Caso I (neve senza vento) - falda 2 (μ1 α2)": _neve("mu1", 2),
                "Caso II (accumulo in valle) - μ2 (α media)": _neve("mu2", 0),
            },
        }
    },
    "Vento": {
        "NTC 2018 - par. 3.3": {
            "Edificio a pianta rettangolare": {
                "(1) Parete sopravento - pressione massima": _vento("parete_sop", "max"),
                "(1) Parete sopravento - pressione media": _vento("parete_sop", "medio"),
                "(2) Copertura sopravento - pressione massima": _vento("copertura_sop", "max"),
                "(2) Copertura sopravento - pressione media": _vento("copertura_sop", "medio"),
                "(3) Copertura sottovento - pressione massima": _vento("copertura_sott", "max"),
                "(3) Copertura sottovento - pressione media": _vento("copertura_sott", "medio"),
                "(4) Parete sottovento - pressione massima": _vento("parete_sott", "max"),
                "(4) Parete sottovento - pressione media": _vento("parete_sott", "medio"),
                "Pressione tangenziale (par. 3.3.5)": _vento("tangenziale"),
            }
        }
    },
}