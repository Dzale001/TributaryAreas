import math

DATABASE = {
    "Solai": {
        "Laterocemento": {
            "DMP Dall'Amora": {
                "12+4 - interasse 50": {
                    "metodo": "fisso",
                    "peso": 240,
                    "spessore": 16,
                    "fonte": "Scheda tecnica DMP Dall'Amora"
                },
                "16+4 - interasse 50": {
                    "metodo": "fisso",
                    "peso": 280,
                    "spessore": 20,
                    "fonte": "Scheda tecnica DMP Dall'Amora"
                },
                "20+4 - interasse 50": {
                    "metodo": "fisso",
                    "peso": 300,
                    "spessore": 24,
                    "fonte": "Scheda tecnica DMP Dall'Amora"
                },
                "12+4 - interasse 60": {
                    "metodo": "fisso",
                    "peso": 200,
                    "spessore": 16,
                    "fonte": "Scheda tecnica DMP Dall'Amora"
                },
                "16+4 - interasse 60": {
                    "metodo": "fisso",
                    "peso": 230,
                    "spessore": 20,
                    "fonte": "Scheda tecnica DMP Dall'Amora"
                },
                "20+4 - interasse 60": {
                    "metodo": "fisso",
                    "peso": 270,
                    "spessore": 24,
                    "fonte": "Scheda tecnica DMP Dall'Amora"
                }
            },
            "Gruppo Ripa Bianca": {
                "12+4 - pannello normale": {
                    "metodo": "fisso",
                    "peso": 250,
                    "spessore": 16,
                    "fonte": "Scheda tecnica Ripa Bianca"
                },
                "16+4 - pannello normale": {
                    "metodo": "fisso",
                    "peso": 300,
                    "spessore": 20,
                    "fonte": "Scheda tecnica Ripa Bianca"
                },
                "20+4 - pannello normale": {
                    "metodo": "fisso",
                    "peso": 340,
                    "spessore": 24,
                    "fonte": "Scheda tecnica Ripa Bianca"
                },
                "24+4 - pannello normale": {
                    "metodo": "fisso",
                    "peso": 380,
                    "spessore": 28,
                    "fonte": "Scheda tecnica Ripa Bianca"
                },
                "28+4 - pannello normale": {
                    "metodo": "fisso",
                    "peso": 420,
                    "spessore": 32,
                    "fonte": "Scheda tecnica Ripa Bianca"
                }
            },
            "Zanutta SPA - Serenissima": {
                # Peso travetto tralicciato: 0.12 kN/ml = 12 kg/ml
                # Fondello: base 12 cm, altezza 4 cm, spessore 1 cm
                # Soletta integrativa: spessore ≥ 4 cm (Rck ≥ 30 N/mm²)
                # Alleggerimenti in laterizio: larghezza 38 cm o 48 cm
                # Interassi ottenibili: 50, 60, 62, 72 cm
                # Peso calcolato: travetto (12 kg/ml) + soletta (4 cm × 2500 kg/m³ = 100 kg/m²)
                #   + blocco laterizio (stimato ~8-10 kg per blocco da 38/48 cm, ~15-20 kg/m²)
                # I valori sotto sono stime conservative da verificare con il produttore.
                "12+4 - interasse 50 (monotrave)": {
                    "metodo": "fisso",
                    "peso": 180,
                    "spessore": 16,
                    "fonte": "Zanutta SPA Serenissima - stima da scheda tecnica (travetto 12 kg/ml + soletta 4 cm + laterizio)"
                },
                "12+4 - interasse 60 (monotrave)": {
                    "metodo": "fisso",
                    "peso": 160,
                    "spessore": 16,
                    "fonte": "Zanutta SPA Serenissima - stima da scheda tecnica (travetto 12 kg/ml + soletta 4 cm + laterizio)"
                },
                "12+4 - interasse 62 (monotrave)": {
                    "metodo": "fisso",
                    "peso": 155,
                    "spessore": 16,
                    "fonte": "Zanutta SPA Serenissima - stima da scheda tecnica (travetto 12 kg/ml + soletta 4 cm + laterizio)"
                },
                "12+4 - interasse 72 (monotrave)": {
                    "metodo": "fisso",
                    "peso": 145,
                    "spessore": 16,
                    "fonte": "Zanutta SPA Serenissima - stima da scheda tecnica (travetto 12 kg/ml + soletta 4 cm + laterizio)"
                }
            }
        },
        "Calcestruzzo":{
            "Progress AG": {
                "Soletta piena":{
                    "metodo": "densita",
                    "densita": 2500,
                    "fonte": "Valore indicativo"}
            }
        }
    },
    "Massetti": {
        "Massetto alleggerito": {
            "Coisoimper": {
                "POLYTECH": {
                    "metodo": "densita",
                    "densita": 400,
                    "fonte": "Scheda tecnica Coisoimper"
                }
            },
            "Leca": {
                "LecaMix Fast": {
                    "metodo": "densita",
                    "densita": 1200,
                    "fonte": "Scheda tecnica Leca"
                }
            }
        },
        "Massetto cementizio": {
            "Tradimalt": {
                "Tradimass": {
                    "metodo": "densita",
                    "densita": 2100,
                    "fonte": "Tradimalt - Manuale tecnico Linea Massetti 2023 (massa volumica prodotto indurito 2100 kg/m³)"
                },
                "Tradimass 2.0": {
                    "metodo": "densita",
                    "densita": 2100,
                    "fonte": "Tradimalt - Manuale tecnico Linea Massetti 2023 (massa volumica > 2100 kg/m³, λ=2.0 W/mK)"
                },
                "Tradimass Dry": {
                    "metodo": "densita",
                    "densita": 2100,
                    "fonte": "Tradimalt - Manuale tecnico Linea Massetti 2023 (massa volumica 2100 kg/m³)"
                },
                "Level": {
                    "metodo": "densita",
                    "densita": 1880,
                    "fonte": "Tradimalt - Manuale tecnico Linea Massetti 2023 (massa volumica 1880 kg/m³, autolivellante 0-15 mm)"
                },
                "Level MAXI": {
                    "metodo": "densita",
                    "densita": 2100,
                    "fonte": "Tradimalt - Manuale tecnico Linea Massetti 2023 (massa volumica 2100 kg/m³, autolivellante 15-50 mm)"
                }
            }
        }
    },

    "Isolanti": {
        "Lana di roccia": {
            "Fassa Bortolo": {
                "Doppia densità": {
                    "metodo": "densita",
                    "densita": 78,
                    "fonte": "Scheda tecnica Fassa Bortolo"
                }
            },
            "Gruppo IVAS": {
                "Monodensità": {
                    "metodo": "densita",
                    "densita": 90,
                    "fonte": "Scheda tecnica IVAS"
                },
                "Doppia densità": {
                    "metodo": "densita",
                    "densita": 78,
                    "fonte": "Scheda tecnica IVAS"
                }
            }
        }
    },
    
# =====================================================
# TAVELLE
# =====================================================

    "Tavelle": {
        "Tavelle in laterizio": {
            "Valori convenzionali": {
                "Tavella 3 cm": {
                    "metodo": "fisso",
                    "peso": 35,
                    "spessore": 3,
                    "fonte": "Valore indicativo da verificare"
                },
                "Tavella 4 cm": {
                    "metodo": "fisso",
                    "peso": 45,
                    "spessore": 4,
                    "fonte": "Valore indicativo da verificare"
                },
                "Tavella 5 cm": {
                    "metodo": "fisso",
                    "peso": 55,
                    "spessore": 5,
                    "fonte": "Valore indicativo da verificare"
                }
            }
        }
    },

# =====================================================
# LATERIZI
# =====================================================

    "Laterizi": {
        "Laterizi forati": {
            "Valori convenzionali": {
                "Laterizio forato leggero": {
                    "metodo": "densita",
                    "densita": 800,
                    "fonte": "Densità indicativa da verificare"
                },
                "Laterizio forato medio": {
                    "metodo": "densita",
                    "densita": 1000,
                    "fonte": "Densità indicativa da verificare"
                },
                "Laterizio forato pesante": {
                    "metodo": "densita",
                    "densita": 1200,
                    "fonte": "Densità indicativa da verificare"
                }
            }
        },
        "Laterizi pieni": {
            "Valori convenzionali": {
                "Mattone pieno": {
                    "metodo": "densita",
                    "densita": 1800,
                    "fonte": "Densità indicativa da verificare"
                }
            }
        },
        "Muri in laterizio": {
            "Valori convenzionali": {
                "Muri in laterizio forato": {
                    "metodo": "muri",
                    "densita": 1000,
                    "fonte": "Densità indicativa da verificare"
                },
                "Muri in mattoni pieni": {
                    "metodo": "muri",
                    "densita": 1800,
                    "fonte": "Densità indicativa da verificare"
                }
            }
        }
    },

# =====================================================
# IMPIANTI
# =====================================================

    "Impianti": {
        "Impianti a pavimento": {
            "Valori convenzionali": {
                "Impianto radiante a pavimento": {
                    "metodo": "fisso",
                    "peso": 15,
                    "fonte": "Valore indicativo da verificare"
                },
                "Impianto idrico sanitario": {
                    "metodo": "fisso",
                    "peso": 10,
                    "fonte": "Valore indicativo da verificare"
                }
            }
        },
        "Impianti elettrici": {
            "Valori convenzionali": {
                "Impianto elettrico sottotraccia": {
                    "metodo": "fisso",
                    "peso": 5,
                    "fonte": "Valore indicativo da verificare"
                }
            }
        },
        "Impianti tecnologici": {
            "Valori convenzionali": {
                "Impianti vari": {
                    "metodo": "fisso",
                    "peso": 10,
                    "fonte": "Valore indicativo da verificare"
                }
            }
        }
    },

# =====================================================
# FRENO AL VAPORE
# =====================================================

    "Freno vapore": {
        "Membrane": {
            "Valori convenzionali": {
                "Membrana freno al vapore PE": {
                    "metodo": "fisso",
                    "peso": 0.20,
                    "spessore": 0.02,
                    "fonte": "Valore indicativo da verificare"
                },
                "Membrana freno al vapore rinforzata": {
                    "metodo": "fisso",
                    "peso": 0.35,
                    "spessore": 0.03,
                    "fonte": "Valore indicativo da verificare"
                },
                "Membrana freno al vapore bituminosa": {
                    "metodo": "fisso",
                    "peso": 3.0,
                    "spessore": 0.3,
                    "fonte": "Valore indicativo da verificare"
                }
            }
        }
    },

# =====================================================
# TEGole
# =====================================================

    "Tegole": {
        "Tegole in laterizio": {
            "Valori convenzionali": {
                "Tegola marsigliese": {
                    "metodo": "fisso",
                    "peso": 45,
                    "fonte": "Valore indicativo da verificare"
                },
                "Tegola portoghese": {
                    "metodo": "fisso",
                    "peso": 42,
                    "fonte": "Valore indicativo da verificare"
                },
                "Coppo tradizionale": {
                    "metodo": "fisso",
                    "peso": 50,
                    "fonte": "Valore indicativo da verificare"
                }
            }
        },
        "Tegole in cemento": {
            "Valori convenzionali": {
                "Tegola in cemento": {
                    "metodo": "fisso",
                    "peso": 48,
                    "fonte": "Valore indicativo da verificare"
                }
            }
        }
    },

# =====================================================
# CORDOLI
# =====================================================

    "Cordoli": {
        "Calcestruzzo": {
            "Valori convenzionali": {
                "Calcestruzzo ordinario": {
                    "metodo": "dimensionale",
                    "densita": 2500,
                    "fonte": "Densità convenzionale"
                },
                "Calcestruzzo armato": {
                    "metodo": "dimensionale",
                    "densita": 2500,
                    "fonte": "Densità convenzionale"
                }
            }
        }
    },

# =====================================================
# TRAVI PRINCIPALI IN LEGNO
# =====================================================

    "Travi principali legno": {
        "Legno massiccio": {
            "Valori convenzionali": {
                "Abete": {
                    "metodo": "travi",
                    "densita": 450,
                    "fonte": "Densità indicativa da verificare"
                },
                "Larice": {
                    "metodo": "travi",
                    "densita": 600,
                    "fonte": "Densità indicativa da verificare"
                },
                "Castagno": {
                    "metodo": "travi",
                    "densita": 650,
                    "fonte": "Densità indicativa da verificare"
                },
                "Rovere": {
                    "metodo": "travi",
                    "densita": 750,
                    "fonte": "Densità indicativa da verificare"
                }
            }
        },
        "Legno lamellare": {
            "Valori convenzionali": {
                "Abete lamellare GL24": {
                    "metodo": "travi",
                    "densita": 450,
                    "fonte": "Valore indicativo da verificare"
                },
                "Abete lamellare GL28": {
                    "metodo": "travi",
                    "densita": 450,
                    "fonte": "Valore indicativo da verificare"
                }
            }
        }
    },

# =====================================================
# TRAVI SECONDARIE IN LEGNO
# =====================================================

    "Travi secondarie legno": {
        "Legno massiccio": {
            "Valori convenzionali": {
                "Abete": {
                    "metodo": "travi",
                    "densita": 450,
                    "fonte": "Densità indicativa da verificare"
                },
                "Larice": {
                    "metodo": "travi",
                    "densita": 600,
                    "fonte": "Densità indicativa da verificare"
                },
                "Castagno": {
                    "metodo": "travi",
                    "densita": 650,
                    "fonte": "Densità indicativa da verificare"
                }
            }
        },
        "Legno lamellare": {
            "Valori convenzionali": {
                "Abete GL24": {
                    "metodo": "travi",
                    "densita": 450,
                    "fonte": "Valore indicativo da verificare"
                }
            }
        }
    },

# =====================================================
# TAVOLATO
# =====================================================

    "Tavolato": {
        "Legno": {
            "Valori convenzionali": {
                "Abete": {
                    "metodo": "densita",
                    "densita": 450,
                    "fonte": "Densità indicativa da verificare"
                },
                "Larice": {
                    "metodo": "densita",
                    "densita": 600,
                    "fonte": "Densità indicativa da verificare"
                },
                "Pino": {
                    "metodo": "densita",
                    "densita": 550,
                    "fonte": "Densità indicativa da verificare"
                },
                "Rovere": {
                    "metodo": "densita",
                    "densita": 750,
                    "fonte": "Densità indicativa da verificare"
                }
            }
        }
    },

# =====================================================
# LAMIERE
# =====================================================

    "Lamiera": {
        "Acciaio": {
            "Isolpack": {
                # --- Lamiere grecate per copertura/parete ---
                # Pesi da "CARATTERISTICHE STATICHE" - colonna Peso [kg/m2]
                # (catalogo Isolpack, schede tecniche pp. 12-34)

                "E/P 3000 - sp. 0,5 mm": {
                    "metodo": "fisso",
                    "peso": 4.6,
                    "spessore": 0.05,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (E/P 3000, tabella proprietà di massa, sp. 0,5 mm)"
                },
                "E/P 3000 - sp. 0,6 mm": {
                    "metodo": "fisso",
                    "peso": 5.6,
                    "spessore": 0.06,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (E/P 3000, sp. 0,6 mm)"
                },
                "E/P 3000 - sp. 0,7 mm": {
                    "metodo": "fisso",
                    "peso": 6.5,
                    "spessore": 0.07,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (E/P 3000, sp. 0,7 mm)"
                },
                "E/P 3000 - sp. 0,8 mm": {
                    "metodo": "fisso",
                    "peso": 7.4,
                    "spessore": 0.08,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (E/P 3000, sp. 0,8 mm)"
                },

                "H20 - sp. 0,5 mm": {
                    "metodo": "fisso",
                    "peso": 5.2,
                    "spessore": 0.05,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (H20, sp. 0,5 mm)"
                },
                "H20 - sp. 0,6 mm": {
                    "metodo": "fisso",
                    "peso": 6.2,
                    "spessore": 0.06,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (H20, sp. 0,6 mm)"
                },
                "H20 - sp. 0,7 mm": {
                    "metodo": "fisso",
                    "peso": 7.3,
                    "spessore": 0.07,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (H20, sp. 0,7 mm)"
                },
                "H20 - sp. 0,8 mm": {
                    "metodo": "fisso",
                    "peso": 8.3,
                    "spessore": 0.08,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (H20, sp. 0,8 mm)"
                },
                "H20 - sp. 1,0 mm": {
                    "metodo": "fisso",
                    "peso": 10.4,
                    "spessore": 0.10,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (H20, sp. 1,0 mm)"
                },

                "SL940 - sp. 0,5 mm": {
                    "metodo": "fisso",
                    "peso": 5.2,
                    "spessore": 0.05,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (SL940, sp. 0,5 mm)"
                },
                "SL940 - sp. 0,6 mm": {
                    "metodo": "fisso",
                    "peso": 6.2,
                    "spessore": 0.06,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (SL940, sp. 0,6 mm)"
                },
                "SL940 - sp. 0,7 mm": {
                    "metodo": "fisso",
                    "peso": 7.2,
                    "spessore": 0.07,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (SL940, sp. 0,7 mm)"
                },
                "SL940 - sp. 0,8 mm": {
                    "metodo": "fisso",
                    "peso": 8.3,
                    "spessore": 0.08,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (SL940, sp. 0,8 mm)"
                },
                "SL940 - sp. 1,0 mm": {
                    "metodo": "fisso",
                    "peso": 10.4,
                    "spessore": 0.10,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (SL940, sp. 1,0 mm)"
                },

                "H28 (900) - sp. 0,5 mm": {
                    "metodo": "fisso",
                    "peso": 5.5,
                    "spessore": 0.05,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (H28, passo 900 mm, sp. 0,5 mm)"
                },
                "H28 (900) - sp. 0,6 mm": {
                    "metodo": "fisso",
                    "peso": 6.5,
                    "spessore": 0.06,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (H28, passo 900 mm, sp. 0,6 mm)"
                },
                "H28 (900) - sp. 0,7 mm": {
                    "metodo": "fisso",
                    "peso": 7.6,
                    "spessore": 0.07,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (H28, passo 900 mm, sp. 0,7 mm)"
                },
                "H28 (900) - sp. 0,8 mm": {
                    "metodo": "fisso",
                    "peso": 8.7,
                    "spessore": 0.08,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (H28, passo 900 mm, sp. 0,8 mm)"
                },
                "H28 (900) - sp. 1,0 mm": {
                    "metodo": "fisso",
                    "peso": 10.9,
                    "spessore": 0.10,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (H28, passo 900 mm, sp. 1,0 mm)"
                },

                "EUROSILMA - sp. 0,5 mm": {
                    "metodo": "fisso",
                    "peso": 5.2,
                    "spessore": 0.05,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (EUROSILMA, sp. 0,5 mm)"
                },
                "EUROSILMA - sp. 0,6 mm": {
                    "metodo": "fisso",
                    "peso": 6.3,
                    "spessore": 0.06,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (EUROSILMA, sp. 0,6 mm)"
                },
                "EUROSILMA - sp. 0,7 mm": {
                    "metodo": "fisso",
                    "peso": 7.3,
                    "spessore": 0.07,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (EUROSILMA, sp. 0,7 mm)"
                },
                "EUROSILMA - sp. 0,8 mm": {
                    "metodo": "fisso",
                    "peso": 8.4,
                    "spessore": 0.08,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (EUROSILMA, sp. 0,8 mm)"
                },
                "EUROSILMA - sp. 1,0 mm": {
                    "metodo": "fisso",
                    "peso": 10.4,
                    "spessore": 0.10,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere grecate (EUROSILMA, sp. 1,0 mm)"
                },

                # --- Lamiere da solaio (gettonate / collaboranti) ---
                # ATTENZIONE: nelle pagine del catalogo estratte non è riportata
                # la tabella "Peso [kg/m2]" per questi profili (pp. 58-90).
                # Inserire i valori dal catalogo completo prima dell'uso.
                "S/C 2000 DECK - sp. da definire": {
                    "metodo": "fisso",
                    "peso": None,
                    "spessore": None,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere da solaio (S/C 2000 DECK, pag. 58) - peso da inserire dal catalogo completo"
                },
                "S/C 2000 - sp. da definire": {
                    "metodo": "fisso",
                    "peso": None,
                    "spessore": None,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere da solaio (S/C 2000, pag. 62) - peso da inserire dal catalogo completo"
                },
                "R/C 400 - sp. da definire": {
                    "metodo": "fisso",
                    "peso": None,
                    "spessore": None,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere da solaio (R/C 400, pag. 66) - peso da inserire dal catalogo completo"
                },
                "E/S 4000 - sp. da definire": {
                    "metodo": "fisso",
                    "peso": None,
                    "spessore": None,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere da solaio (E/S 4000, pag. 70) - peso da inserire dal catalogo completo"
                },
                "LG 55 600/750 - sp. da definire": {
                    "metodo": "fisso",
                    "peso": None,
                    "spessore": None,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere da solaio (LG 55 600/750, pag. 74) - peso da inserire dal catalogo completo"
                },
                "LG 75 - sp. da definire": {
                    "metodo": "fisso",
                    "peso": None,
                    "spessore": None,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere da solaio (LG 75, pag. 78) - peso da inserire dal catalogo completo"
                },
                "TECNODEC 105 - sp. da definire": {
                    "metodo": "fisso",
                    "peso": None,
                    "spessore": None,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere da solaio (TECNODEC 105, pag. 82) - peso da inserire dal catalogo completo"
                },
                "TECNODEC 150 - sp. da definire": {
                    "metodo": "fisso",
                    "peso": None,
                    "spessore": None,
                    "fonte": "Isolpack - Catalogo tecnico Lamiere da solaio (TECNODEC 150, pag. 86) - peso da inserire dal catalogo completo"
                }
            }
        },

        "Alluminio": {
            "Isolpack": {
                # Il catalogo Isolpack riporta solo tabelle di portata per
                # alluminio lega 3105, non una tabella "Peso [kg/m2]".
                # I valori seguenti sono calcolati analiticamente:
                # peso [kg/m2] = spessore [mm] x densità alluminio (2700 kg/m3)
                #   sp. 0,8 mm -> 2,16 kg/m2
                #   sp. 1,0 mm -> 2,70 kg/m2
                "Lamiera alluminio 0,8 mm": {
                    "metodo": "fisso",
                    "peso": 2.16,
                    "spessore": 0.08,
                    "fonte": "Calcolo da spessore x densità alluminio 2700 kg/m3 (Isolpack lega 3105) - verificare con produttore"
                },
                "Lamiera alluminio 1,0 mm": {
                    "metodo": "fisso",
                    "peso": 2.70,
                    "spessore": 0.10,
                    "fonte": "Calcolo da spessore x densità alluminio 2700 kg/m3 (Isolpack lega 3105) - verificare con produttore"
                }
            }
        }
    },

# =====================================================
# INTONACO
# =====================================================

    "Intonaco": {
        "Intonaci tradizionali": {
            "Valori convenzionali": {
                "Intonaco civile": {
                    "metodo": "densita",
                    "densita": 1800,
                    "fonte": "Densità indicativa da verificare"
                },
                "Intonaco premiscelato": {
                    "metodo": "densita",
                    "densita": 1400,
                    "fonte": "Densità indicativa da verificare"
                },
                "Intonaco a base gesso": {
                    "metodo": "densita",
                    "densita": 1000,
                    "fonte": "Densità indicativa da verificare"
                }
            }
        }
    },

# =====================================================
# FINITURE
# =====================================================

    "Finiture": {
        "Pavimentazioni": {
            "Valori convenzionali": {
                "Gres porcellanato": {
                    "metodo": "densita",
                    "densita": 2300,
                    "fonte": "Densità indicativa da verificare"
                },
                "Ceramica": {
                    "metodo": "densita",
                    "densita": 2200,
                    "fonte": "Densità indicativa da verificare"
                },
                "Marmo": {
                    "metodo": "densita",
                    "densita": 2700,
                    "fonte": "Densità indicativa da verificare"
                },
                "Parquet": {
                    "metodo": "densita",
                    "densita": 700,
                    "fonte": "Densità indicativa da verificare"
                },
                "Pietra naturale": {
                    "metodo": "densita",
                    "densita": 2600,
                    "fonte": "Densità indicativa da verificare"
                }
            }
        },
        "Rivestimenti": {
            "Valori convenzionali": {
                "Rivestimento ceramico": {
                    "metodo": "densita",
                    "densita": 2200,
                    "fonte": "Densità indicativa da verificare"
                },
                "Rivestimento in pietra": {
                    "metodo": "densita",
                    "densita": 2600,
                    "fonte": "Densità indicativa da verificare"
                }
            }
        }
    },

# =====================================================
# SOVRACCARICHI
# =====================================================

        "Sovraccarico": {
            "Ambienti ad uso residenziale": {
                "NTC 2018 - Categoria A": {
                    "Aree per attività domestiche": {
                        "metodo": "fisso",
                        "tipo_calcolo": "sovraccarico",
                        "peso": 204,
                        "fonte": "NTC 2018 - Cat. A - 2.00 kN/m² (≈204 kg/m²)"
                    },
                    "Scale comuni e balconi": {
                        "metodo": "fisso",
                        "tipo_calcolo": "sovraccarico",
                        "peso": 408,
                        "fonte": "NTC 2018 - Cat. A - 4.00 kN/m² (≈408 kg/m²)"
                    }
                }
            },
            "Uffici": {
                "NTC 2018 - Categoria B": {
                    "B1 - Uffici non aperti al pubblico": {
                        "metodo": "fisso",
                        "tipo_calcolo": "sovraccarico",
                        "peso": 204,
                        "fonte": "NTC 2018 - Cat. B1 - 2.00 kN/m² (≈204 kg/m²)"
                    },
                    "B2 - Uffici aperti al pubblico": {
                        "metodo": "fisso",
                        "tipo_calcolo": "sovraccarico",
                        "peso": 306,
                        "fonte": "NTC 2018 - Cat. B2 - 3.00 kN/m² (≈306 kg/m²)"
                    },
                    "Scale comuni, terrazze e ballatoi": {
                        "metodo": "fisso",
                        "tipo_calcolo": "sovraccarico",
                        "peso": 408,
                        "fonte": "NTC 2018 - Cat. B - 4.00 kN/m² (≈408 kg/m²)"
                    }
                }
            },
            "Ambienti suscettibili di affollamento": {
                "NTC 2018 - Categoria C": {
                    "C1 - Aree con tavoli (scuole, caffè, ristoranti, sale banchetti, lettura, ricevimento)": {
                        "metodo": "fisso",
                        "tipo_calcolo": "sovraccarico",
                        "peso": 306,
                        "fonte": "NTC 2018 - Cat. C1 - 3.00 kN/m² (≈306 kg/m²)"
                    },
                    "C2 - Aree con posti a sedere fissi (chiese, teatri, cinema, sale conferenze, aule universitarie)": {
                        "metodo": "fisso",
                        "tipo_calcolo": "sovraccarico",
                        "peso": 408,
                        "fonte": "NTC 2018 - Cat. C2 - 4.00 kN/m² (≈408 kg/m²)"
                    },
                    "C3 - Aree prive di ostacoli per il movimento delle persone (musei, sale per esposizioni, aree d'ingresso a uffici, alberghi, ospedali, atri di stazioni ferroviarie)": {
                        "metodo": "fisso",
                        "tipo_calcolo": "sovraccarico",
                        "peso": 510,
                        "fonte": "NTC 2018 - Cat. C3 - 5.00 kN/m² (≈510 kg/m²)"
                    },
                    "C4 - Aree con possibile svolgimento di attività fisiche (sale da ballo, palestre, palcoscenici)": {
                        "metodo": "fisso",
                        "tipo_calcolo": "sovraccarico",
                        "peso": 510,
                        "fonte": "NTC 2018 - Cat. C4 - 5.00 kN/m² (≈510 kg/m²)"
                    },
                    "C5 - Aree suscettibili di grandi affollamenti (edifici per eventi pubblici, sale da concerto, palazzetti per sport, tribune, gradinate, piattaforme ferroviarie)": {
                        "metodo": "fisso",
                        "tipo_calcolo": "sovraccarico",
                        "peso": 510,
                        "fonte": "NTC 2018 - Cat. C5 - 5.00 kN/m² (≈510 kg/m²)"
                    },
                    "Scale comuni, balconi, ballatoi": {
                        "metodo": "fisso",
                        "tipo_calcolo": "sovraccarico",
                        "peso": 408,
                        "fonte": "NTC 2018 - Cat. C - 4.00 kN/m² (≈408 kg/m²)"
                    }
                }
            },
            "Aree ad uso commerciale": {
                "NTC 2018 - Categoria D": {
                    "D1 - Negozi": {
                        "metodo": "fisso",
                        "tipo_calcolo": "sovraccarico",
                        "peso": 408,
                        "fonte": "NTC 2018 - Cat. D1 - 4.00 kN/m² (≈408 kg/m²)"
                    },
                    "D2 - Centri commerciali, mercati, grandi magazzini": {
                        "metodo": "fisso",
                        "tipo_calcolo": "sovraccarico",
                        "peso": 510,
                        "fonte": "NTC 2018 - Cat. D2 - 5.00 kN/m² (≈510 kg/m²)"
                    },
                    "Scale comuni, balconi, ballatoi": {
                        "metodo": "fisso",
                        "tipo_calcolo": "sovraccarico",
                        "peso": 408,
                        "fonte": "NTC 2018 - Cat. D - 4.00 kN/m² (≈408 kg/m²)"
                    }
                }
            },
            "Aree per immagazzinamento e uso commerciale ed uso industriale": {
                "NTC 2018 - Categoria E": {
                    "E1 - Aree per accumulo di merci e relative aree d'accesso (biblioteche, archivi, magazzini, depositi, laboratori manifatturieri)": {
                        "metodo": "fisso",
                        "tipo_calcolo": "sovraccarico",
                        "peso": 714,
                        "fonte": "NTC 2018 - Cat. E1 - ≥6.00 kN/m² (≈714 kg/m²) - da valutare caso per caso"
                    },
                    "E2 - Ambienti ad uso industriale": {
                        "metodo": "fisso",
                        "tipo_calcolo": "sovraccarico",
                        "peso": 714,
                        "fonte": "NTC 2018 - Cat. E2 - ≥6.00 kN/m² (≈714 kg/m²) - da valutare caso per caso"
                    }
                }
            },
            "Rimesse e aree per traffico di veicoli (esclusi i ponti)": {
                "NTC 2018 - Categoria F-G": {
                    "F - Rimesse, aree per parcheggio e sosta di veicoli (peso complessivo ≤30 kN)": {
                        "metodo": "fisso",
                        "tipo_calcolo": "sovraccarico",
                        "peso": 255,
                        "fonte": "NTC 2018 - Cat. F - 2.50 kN/m² (≈255 kg/m²) - da valutare caso per caso"
                    },
                    "G - Aree per parcheggio e sosta di veicoli medi (30 kN < peso complessivo ≤160 kN, rampe d'accesso, zone di carico e scarico)": {
                        "metodo": "fisso",
                        "tipo_calcolo": "sovraccarico",
                        "peso": 510,
                        "fonte": "NTC 2018 - Cat. G - 5.00 kN/m² (≈510 kg/m²) - da valutare caso per caso"
                    }
                }
            },
            "Coperture": {
                "NTC 2018 - Categoria H-I-K": {
                    "H - Coperture accessibili per sola manutenzione e riparazione": {
                        "metodo": "fisso",
                        "tipo_calcolo": "sovraccarico",
                        "peso": 51,
                        "fonte": "NTC 2018 - Cat. H - 0.50 kN/m² (≈51 kg/m²) - secondo la categoria di appartenenza"
                    },
                    "I - Coperture praticabili di ambienti di categoria A-D (esclusi H)": {
                        "metodo": "fisso",
                        "tipo_calcolo": "sovraccarico",
                        "peso": 102,
                        "fonte": "NTC 2018 - Cat. I - 1.00 kN/m² (≈102 kg/m²) - secondo la categoria di appartenenza"
                    },
                    "K - Coperture per usi speciali (impianti, eliporti)": {
                        "metodo": "fisso",
                        "tipo_calcolo": "sovraccarico",
                        "peso": 102,
                        "fonte": "NTC 2018 - Cat. K - 1.00 kN/m² (≈102 kg/m²) - da valutare caso per caso"
                    }
                }
            }
        }

}

import math   # <-- in cima al file

# =====================================================
# TRAVI IN ACCIAIO (IPE, HEA, omega, tubolari)
# =====================================================
# metodo "profilo": peso_lineare [kg/m] del singolo profilo,
# h_cm e b_cm (altezza e larghezza) per il disegno.

_DENSITA_ACCIAIO = 7850  # kg/m³

# n: (peso kg/m, altezza mm, larghezza mm)
_IPE = {
    80: (6.0, 80, 46),    100: (8.1, 100, 55),  120: (10.4, 120, 64),
    140: (12.9, 140, 73), 160: (15.8, 160, 82), 180: (18.8, 180, 91),
    200: (22.4, 200, 100), 220: (26.2, 220, 110), 240: (30.7, 240, 120),
    270: (36.1, 270, 135), 300: (42.2, 300, 150), 330: (49.1, 330, 160),
    360: (57.1, 360, 170), 400: (66.3, 400, 180), 450: (77.6, 450, 190),
    500: (90.7, 500, 200), 550: (106.0, 550, 210), 600: (122.0, 600, 220),
}
_HEA = {
    100: (16.7, 96, 100),  120: (19.9, 114, 120), 140: (24.7, 133, 140),
    160: (30.4, 152, 160), 180: (35.5, 171, 180), 200: (42.3, 190, 200),
    220: (50.5, 210, 220), 240: (60.3, 230, 240), 260: (68.2, 250, 260),
    280: (76.4, 270, 280), 300: (88.3, 290, 300), 320: (97.6, 310, 300),
    340: (105.0, 330, 300), 360: (112.0, 350, 300), 400: (125.0, 390, 300),
    450: (140.0, 440, 300), 500: (155.0, 490, 300), 550: (166.0, 540, 300),
    600: (178.0, 590, 300),
}

# Omega a freddo: (h mm, base superiore mm, ali mm cad.)
_OMEGA_GEOM = [(30, 40, 20), (40, 60, 20), (50, 60, 25), (60, 80, 30)]
_OMEGA_SPESSORI = [1.0, 1.5, 2.0, 3.0]   # mm


def _omega_peso(h, b, f, t):
    sviluppo_mm = b + 2 * h + 2 * f
    return sviluppo_mm * t * 1e-6 * _DENSITA_ACCIAIO   # kg/m


# ---- Tubolari a freddo (EN 10219) ----
def _raggio_est(t):
    """Raggio esterno degli spigoli: 1.5t (t<=6), 2t (6<t<=10), 2.5t (t>10)."""
    if t <= 6:
        return 1.5 * t
    return 2.0 * t if t <= 10 else 2.5 * t


def _peso_rettangolare(h, b, t):
    ro = _raggio_est(t)
    ri = ro - t
    area = 2 * t * (h + b - 2 * t) - (4 - math.pi) * (ro ** 2 - ri ** 2)  # mm²
    return area * 1e-6 * _DENSITA_ACCIAIO


def _peso_circolare(d, t):
    return math.pi * (d - t) * t * 1e-6 * _DENSITA_ACCIAIO


# (lato mm, spessore mm)
_QUADRI = [
    (40, 2), (40, 3), (50, 3), (60, 3), (80, 3), (80, 4), (100, 4), (100, 5),
    (120, 5), (120, 6), (150, 5), (150, 6), (150, 8), (200, 6), (200, 8), (200, 10),
]
# (altezza mm, base mm, spessore mm)
_RETTANGOLARI = [
    (60, 40, 3), (80, 40, 3), (100, 50, 3), (100, 50, 4), (120, 60, 4),
    (120, 80, 5), (150, 100, 5), (160, 80, 5), (200, 100, 6), (200, 120, 8),
]
# (diametro esterno mm, spessore mm)
_CIRCOLARI = [
    (33.7, 3.2), (42.4, 3.2), (48.3, 3.2), (60.3, 3.2), (76.1, 3.2),
    (88.9, 4.0), (101.6, 4.0), (114.3, 4.0), (139.7, 5.0), (168.3, 5.0),
    (193.7, 6.3), (219.1, 6.3), (273.0, 6.3),
]

_FONTE_TUBI = "Calcolo geometrico da dimensioni nominali (EN 10219, acciaio 7850 kg/m³) - verificare con scheda del produttore"

DATABASE["Travi acciaio"] = {
    "IPE": {
        "Profilario UNI EN 10365": {
            f"IPE {n}": {
                "metodo": "profilo", "peso_lineare": p,
                "h_cm": h / 10, "b_cm": b / 10,
                "fonte": "Profilario europeo IPE (UNI EN 10365) - peso nominale"
            }
            for n, (p, h, b) in _IPE.items()
        }
    },
    "HEA": {
        "Profilario UNI EN 10365": {
            f"HEA {n}": {
                "metodo": "profilo", "peso_lineare": p,
                "h_cm": h / 10, "b_cm": b / 10,
                "fonte": "Profilario europeo HEA (UNI EN 10365) - peso nominale"
            }
            for n, (p, h, b) in _HEA.items()
        }
    },
    "Omega": {
        "Calcolo geometrico": {
            f"Omega h{h} x {b} (ali {f}) - sp. {t:.1f} mm": {
                "metodo": "profilo",
                "peso_lineare": round(_omega_peso(h, b, f, t), 2),
                "h_cm": h / 10, "b_cm": (b + 2 * f) / 10,
                "fonte": "Calcolo: sviluppo x spessore x 7850 kg/m³ - sostituire con scheda del produttore"
            }
            for (h, b, f) in _OMEGA_GEOM
            for t in _OMEGA_SPESSORI
        }
    },
    "Tubolare quadro": {
        "Calcolo geometrico (EN 10219)": {
            f"Tubolare {a} x {a} x {t:g}": {
                "metodo": "profilo",
                "peso_lineare": round(_peso_rettangolare(a, a, t), 2),
                "h_cm": a / 10, "b_cm": a / 10,
                "fonte": _FONTE_TUBI
            }
            for (a, t) in _QUADRI
        }
    },
    "Tubolare rettangolare": {
        "Calcolo geometrico (EN 10219)": {
            f"Tubolare {h} x {b} x {t:g}": {
                "metodo": "profilo",
                "peso_lineare": round(_peso_rettangolare(h, b, t), 2),
                "h_cm": h / 10, "b_cm": b / 10,
                "fonte": _FONTE_TUBI
            }
            for (h, b, t) in _RETTANGOLARI
        }
    },
    "Tubo circolare": {
        "Calcolo geometrico (EN 10219)": {
            f"Tubo Ø{d:g} x {t:g}": {
                "metodo": "profilo",
                "peso_lineare": round(_peso_circolare(d, t), 2),
                "h_cm": d / 10, "b_cm": d / 10,
                "fonte": _FONTE_TUBI
            }
            for (d, t) in _CIRCOLARI
        }
    },
}

from azioni_climatiche import VOCI_CLIMATICHE
DATABASE.update(VOCI_CLIMATICHE)