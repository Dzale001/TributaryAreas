import sys
import zlib

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPolygonF, QPalette, QFontMetrics
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSizePolicy,
    QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QComboBox, QDoubleSpinBox,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGroupBox
)

from database_materiali import DATABASE

G = 9.81  # m/s²


class StratigrafiaWidget(QWidget):
    """Disegno schematico (non in scala) della stratigrafia, dall'alto verso il basso."""

    ALTEZZA_MIN = 30        # px minimi per strato (servono per le etichette)
    N_RIPETIZIONI = 4       # quante travi/muri si disegnano nello schema

    def __init__(self):
        super().__init__()
        self.strati = []
        self.selezionato = -1
        self.setMinimumSize(340, 300)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

    def set_strati(self, strati):
        self.strati = list(strati)
        if self.selezionato >= len(self.strati):
            self.selezionato = -1
        self.update()

    def set_selezione(self, riga):
        self.selezionato = riga
        self.update()

    @staticmethod
    def _colore(categoria):
        # tinta stabile per categoria (crc32 non cambia tra un avvio e l'altro)
        tinta = zlib.crc32(categoria.encode("utf-8")) % 360
        return QColor.fromHsv(tinta, 90, 225)

    def _altezze(self, n, spessori, altezza_totale):
        """Altezze in px: scala compressa (radice) + minimo leggibile."""
        if n == 0:
            return []
        if altezza_totale <= n * self.ALTEZZA_MIN:
            return [altezza_totale / n] * n
        raw = [max(t, 0.5) ** 0.5 for t in spessori]
        somma = sum(raw)
        extra = altezza_totale - n * self.ALTEZZA_MIN
        return [self.ALTEZZA_MIN + r / somma * extra for r in raw]

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        pal = self.palette()
        colore_testo = pal.color(QPalette.ColorRole.Text)
        colore_tenue = pal.color(QPalette.ColorRole.PlaceholderText)
        scuro = QColor(40, 40, 40)

        p.fillRect(self.rect(), pal.color(QPalette.ColorRole.Base))

        if not self.strati:
            p.setPen(colore_tenue)
            p.drawText(
                self.rect(), Qt.AlignmentFlag.AlignCenter,
                "Aggiungi dei materiali\nper vedere la stratigrafia"
            )
            return

        margine = 12
        larg_sez = int(self.width() * 0.46)
        x0 = margine
        x_etichette = x0 + larg_sez + 26
        larg_etichette = self.width() - x_etichette - margine

        fisici = [
            (i, s) for i, s in enumerate(self.strati)
            if s.get("tipo_disegno") != "sovraccarico"
        ]
        carichi = [
            s for s in self.strati if s.get("tipo_disegno") == "sovraccarico"
        ]

        font_piccolo = self.font()
        font_piccolo.setPointSizeF(max(font_piccolo.pointSizeF() - 1, 7))
        p.setFont(font_piccolo)
        fm = QFontMetrics(font_piccolo)

        y = margine

        # ---- sovraccarichi: frecce sopra la stratigrafia ----
        if carichi:
            q = sum(c["valore"] for c in carichi)
            p.setPen(colore_testo)
            p.drawText(
                QRectF(x0, y, self.width() - 2 * margine, fm.height()),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                f"Sovraccarico q = {q:.2f} kN/m²"
            )
            y_freccia_in = y + fm.height() + 2
            y_freccia_fin = y_freccia_in + 22
            p.setPen(QPen(QColor(200, 60, 60), 1.5))
            p.setBrush(QColor(200, 60, 60))
            for k in range(6):
                xf = x0 + (k + 0.5) * larg_sez / 6
                p.drawLine(QPointF(xf, y_freccia_in), QPointF(xf, y_freccia_fin - 4))
                p.drawPolygon(QPolygonF([
                    QPointF(xf - 4, y_freccia_fin - 6),
                    QPointF(xf + 4, y_freccia_fin - 6),
                    QPointF(xf, y_freccia_fin),
                ]))
            y = y_freccia_fin + 6

        # ---- strati ----
        basso = self.height() - margine - fm.height() - 4
        altezze = self._altezze(
            len(fisici),
            [s.get("spessore_cm", 2.0) for _, s in fisici],
            basso - y
        )

        for (indice, s), h in zip(fisici, altezze):
            banda = QRectF(x0, y, larg_sez, h)
            colore = self._colore(s["categoria"])
            tipo = s.get("tipo_disegno", "continuo")

            p.setPen(QPen(scuro, 1))

            if tipo in ("travi", "muri"):
                # sfondo chiaro + elementi ripetuti a passo costante
                p.setBrush(colore.lighter(125))
                p.drawRect(banda)

                passo = larg_sez / self.N_RIPETIZIONI
                rapporto = s["b_cm"] / s["interasse_cm"] if s["interasse_cm"] else 0.2
                larg_el = min(max(rapporto * passo, 6), passo * 0.85)

                if tipo == "muri":
                    p.setBrush(QBrush(colore.darker(130), Qt.BrushStyle.DiagCrossPattern))
                else:
                    p.setBrush(colore.darker(115))

                for k in range(self.N_RIPETIZIONI):
                    cx = x0 + passo * (k + 0.5)
                    p.drawRect(QRectF(cx - larg_el / 2, y, larg_el, h))

            elif tipo == "blocco":
                # elemento singolo (es. cordolo): blocco a sinistra
                p.setBrush(colore.lighter(125))
                p.drawRect(banda)
                p.setBrush(colore.darker(115))
                p.drawRect(QRectF(x0, y, larg_sez * 0.25, h))

            else:
                p.setBrush(colore)
                p.drawRect(banda)
                if tipo == "fisso":
                    p.setBrush(QBrush(colore.darker(125), Qt.BrushStyle.BDiagPattern))
                    p.drawRect(banda)

            # evidenzia lo strato selezionato in tabella
            if indice == self.selezionato:
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(QColor(30, 110, 220), 3))
                p.drawRect(banda)

            # etichetta a destra con linea di richiamo
            y_mezzo = y + h / 2
            p.setPen(QPen(colore_tenue, 1))
            p.drawLine(QPointF(x0 + larg_sez, y_mezzo), QPointF(x_etichette - 4, y_mezzo))

            riga1 = s["etichetta"]
            riga2 = f'{s["valore"]:.1f} {s["unita"]}'
            if s.get("dimensioni", "-") != "-":
                riga2 = f'{s["dimensioni"]}  |  {riga2}'

            p.setPen(colore_testo)
            testo = (
                fm.elidedText(riga1, Qt.TextElideMode.ElideRight, int(larg_etichette))
                + "\n"
                + fm.elidedText(riga2, Qt.TextElideMode.ElideRight, int(larg_etichette))
            )
            p.drawText(
                QRectF(x_etichette, y, larg_etichette, h),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                testo
            )

            y += h

        # ---- nota a piè ----
        p.setPen(colore_tenue)
        p.drawText(
            QRectF(x0, self.height() - margine - fm.height(),
                   self.width() - 2 * margine, fm.height()),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            "Schema non in scala - dall'alto verso il basso come in tabella"
        )


class LoadViewer(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Calcolo carichi - Materiali")
        self.resize(1250, 850)

        self.strati = []

        self.crea_interfaccia()
        self.aggiorna_categorie()

    # -------------------------------------------------
    # UTILITÀ
    # -------------------------------------------------

    @staticmethod
    def _spin(minimo, massimo, decimali, valore, suffisso=""):
        s = QDoubleSpinBox()
        s.setRange(minimo, massimo)
        s.setDecimals(decimali)
        s.setValue(valore)
        if suffisso:
            s.setSuffix(suffisso)
        return s

    @staticmethod
    def _imposta(spin, valore, suffisso=None):
        """Imposta un valore senza far scattare i segnali (evita ricalcoli a catena)."""
        spin.blockSignals(True)
        if suffisso is not None:
            spin.setSuffix(suffisso)
        spin.setValue(valore)
        spin.blockSignals(False)

    # -------------------------------------------------
    # INTERFACCIA
    # -------------------------------------------------

    def crea_interfaccia(self):

        centrale = QWidget()
        self.setCentralWidget(centrale)
        layout = QVBoxLayout(centrale)

        # ---------- SELEZIONE MATERIALE ----------
        gruppo = QGroupBox("Selezione materiale")
        form = QFormLayout(gruppo)
        self.form = form

        self.categoria = QComboBox()
        self.tipo = QComboBox()
        self.produttore = QComboBox()
        self.prodotto = QComboBox()

        self.categoria.currentTextChanged.connect(self.aggiorna_tipi)
        self.tipo.currentTextChanged.connect(self.aggiorna_produttori)
        self.produttore.currentTextChanged.connect(self.aggiorna_prodotti)
        self.prodotto.currentTextChanged.connect(self.aggiorna_dati)

        form.addRow("Categoria:", self.categoria)
        form.addRow("Tipologia:", self.tipo)
        form.addRow("Produttore:", self.produttore)
        form.addRow("Prodotto:", self.prodotto)

        # ---------- DATI MODIFICABILI ----------
        # Densità (materiali a densità, elementi dimensionali, travi)
        self.densita = self._spin(0, 30000, 1, 0, " kg/m³")
        form.addRow("Densità:", self.densita)

        # Peso dichiarato (materiali a peso fisso / sovraccarichi)
        self.peso_fisso = self._spin(0, 100000, 3, 0, " kg/m²")
        form.addRow("Peso dichiarato:", self.peso_fisso)

        # Spessore (materiali a densità)
        self.spessore = self._spin(0, 200, 2, 5, " cm")
        form.addRow("Spessore:", self.spessore)

        # Sezione dell'elemento (travi, cordoli)
        self.larghezza_elemento = self._spin(0.01, 500, 2, 20, " cm")
        self.altezza_elemento = self._spin(0.01, 500, 2, 30, " cm")
        form.addRow("Larghezza elemento (b):", self.larghezza_elemento)
        form.addRow("Altezza elemento (h):", self.altezza_elemento)

        # Numero elementi (solo elementi lineari tipo cordoli)
        self.numero_elementi = self._spin(1, 1000, 0, 1)
        form.addRow("Numero elementi:", self.numero_elementi)

        # Peso al metro del singolo profilo (travi in acciaio)
        # Profili in acciaio: peso al metro + modalità di calcolo
        self.modo_profilo = QComboBox()
        self.modo_profilo.addItems([
            "Elementi singoli (n. profili)",
            "Ripetuti a interasse"
        ])
        self.modo_profilo.currentIndexChanged.connect(self.cambia_modo_profilo)
        form.addRow("Profili - modalità:", self.modo_profilo)

        self.peso_profilo = self._spin(0, 5000, 2, 0, " kg/m")
        form.addRow("Peso profilo (singolo):", self.peso_profilo)

        # Travi: interasse oppure numero di travi al metro
        self.modo_interasse = QComboBox()
        self.modo_interasse.addItems(["Interasse", "N. travi per metro"])
        self.modo_interasse.currentIndexChanged.connect(self.cambia_modo_interasse)

        self.valore_interasse = self._spin(1, 1000, 2, 50, " cm")

        form.addRow("Travi - dato noto:", self.modo_interasse)
        form.addRow("Travi - valore:", self.valore_interasse)

        self.info_travi = QLabel("-")
        form.addRow("Travi - equivalenza:", self.info_travi)

        # ---------- INFORMAZIONI ----------
        self.fonte_label = QLabel("-")
        self.peso_label = QLabel("0 kg/m²")

        form.addRow("Fonte:", self.fonte_label)
        form.addRow("Peso calcolato:", self.peso_label)

        # Ricalcolo a ogni modifica
        for spin in (
            self.densita, self.peso_fisso, self.spessore,
            self.larghezza_elemento, self.altezza_elemento,
            self.numero_elementi, self.valore_interasse,
            self.peso_profilo
        ):
            spin.valueChanged.connect(self.calcola_peso)

        layout.addWidget(gruppo)

        # ---------- PULSANTE AGGIUNGI ----------
        self.btn_aggiungi = QPushButton("Aggiungi materiale alla stratigrafia")
        self.btn_aggiungi.clicked.connect(self.aggiungi_materiale)
        layout.addWidget(self.btn_aggiungi)

        # ---------- TABELLA STRATI ----------
        self.tabella = QTableWidget(0, 6)
        self.tabella.setHorizontalHeaderLabels([
            "Categoria", "Materiale", "Dimensioni",
            "Valore", "Unità", "Fonte"
        ])
        intest = self.tabella.horizontalHeader()
        for col in range(6):
            intest.setSectionResizeMode(
                col,
                QHeaderView.ResizeMode.Stretch if col in (1, 5)
                else QHeaderView.ResizeMode.ResizeToContents
            )
        self.tabella.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tabella.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        # canvas della stratigrafia accanto alla tabella
        self.canvas = StratigrafiaWidget()
        self.tabella.currentCellChanged.connect(
            lambda riga, *_: self.canvas.set_selezione(riga)
        )

        riga_tabella = QHBoxLayout()
        riga_tabella.addWidget(self.tabella, 1)
        riga_tabella.addWidget(self.canvas, 1)
        layout.addLayout(riga_tabella)

        # ---------- RIMOZIONE ----------
        btn_rimuovi = QPushButton("Rimuovi materiale selezionato")
        btn_rimuovi.clicked.connect(self.rimuovi_materiale)
        layout.addWidget(btn_rimuovi)

        # ---------- RISULTATI ----------
        gruppo_finale = QGroupBox("Risultati")
        finale = QFormLayout(gruppo_finale)

        self.totale_kg = QLabel("0 kg/m²")
        self.totale_kn = QLabel("0 kN/m²")

        self.larghezza = self._spin(0.01, 100, 2, 1.0, " m")
        self.larghezza.valueChanged.connect(self.aggiorna_totali)

        self.carico_lineare = QLabel("0 kN/m")
        self.peso_lineare = QLabel("0 kg/m")
        self.sovraccarico = QLabel("0 kN/m²")
        self.carico_permanente = QLabel("0 kN/m")

        finale.addRow("Peso totale:", self.totale_kg)
        finale.addRow("Carico superficiale:", self.totale_kn)
        finale.addRow("Larghezza di influenza:", self.larghezza)
        finale.addRow("Carico lineare:", self.carico_lineare)
        finale.addRow("Peso elementi lineari:", self.peso_lineare)
        finale.addRow("Sovraccarico:", self.sovraccarico)
        finale.addRow("Carico permanente lineare:", self.carico_permanente)

        layout.addWidget(gruppo_finale)

        self.aggiorna_abilitazioni(None)

    # -------------------------------------------------
    # AGGIORNAMENTO COMBOBOX
    # -------------------------------------------------

    def aggiorna_categorie(self):
        self.categoria.clear()
        self.categoria.addItems(DATABASE.keys())

    def aggiorna_tipi(self):
        self.tipo.clear()
        categoria = self.categoria.currentText()
        if categoria:
            self.tipo.addItems(DATABASE[categoria].keys())

    def aggiorna_produttori(self):
        self.produttore.clear()
        categoria = self.categoria.currentText()
        tipo = self.tipo.currentText()
        if categoria and tipo:
            self.produttore.addItems(DATABASE[categoria][tipo].keys())

    def aggiorna_prodotti(self):
        self.prodotto.clear()
        categoria = self.categoria.currentText()
        tipo = self.tipo.currentText()
        produttore = self.produttore.currentText()
        if categoria and tipo and produttore:
            self.prodotto.addItems(DATABASE[categoria][tipo][produttore].keys())

    # -------------------------------------------------
    # LETTURA DATI
    # -------------------------------------------------

    def get_materiale(self):
        try:
            categoria = self.categoria.currentText()
            tipo = self.tipo.currentText()
            produttore = self.produttore.currentText()
            prodotto = self.prodotto.currentText()

            materiale = DATABASE[categoria][tipo][produttore][prodotto]

            if not isinstance(materiale, dict):
                return None
            return materiale

        except (KeyError, TypeError):
            return None

    @staticmethod
    def _e_sovraccarico(materiale):
        return materiale.get("tipo_calcolo") == "sovraccarico"

    # -------------------------------------------------
    # ABILITAZIONE CAMPI IN BASE AL METODO
    # -------------------------------------------------

    def aggiorna_abilitazioni(self, materiale):
        metodo = materiale.get("metodo") if materiale else None
        sovraccarico = bool(materiale) and self._e_sovraccarico(materiale)

        usa_densita = metodo in ("densita", "dimensionale", "travi", "muri")
        usa_peso = metodo == "fisso" or sovraccarico

        profilo = metodo == "profilo"
        distribuito = profilo and self.modo_profilo.currentIndex() == 1

        self.densita.setEnabled(usa_densita)
        self.peso_fisso.setEnabled(usa_peso)
        self.spessore.setEnabled(metodo == "densita")
        self.larghezza_elemento.setEnabled(metodo in ("dimensionale", "travi", "muri"))
        self.altezza_elemento.setEnabled(metodo in ("dimensionale", "travi", "muri"))

        # n. elementi: cordoli, oppure profili singoli (non a interasse)
        self.numero_elementi.setEnabled(
            metodo == "dimensionale" or (profilo and not distribuito)
        )
        self.modo_profilo.setEnabled(profilo)
        self.peso_profilo.setEnabled(profilo)

        # interasse: travi, muri, oppure profili ripetuti a interasse
        usa_interasse = metodo in ("travi", "muri") or distribuito
        self.modo_interasse.setEnabled(usa_interasse)
        self.valore_interasse.setEnabled(usa_interasse)

    def aggiorna_dati(self):

        materiale = self.get_materiale()
        if not materiale:
            self.aggiorna_abilitazioni(None)
            return

        metodo = materiale.get("metodo")
        self.aggiorna_abilitazioni(materiale)

        # Valori di partenza presi dal database (poi modificabili a mano)
        self.aggiorna_etichette(metodo)

        if metodo in ("densita", "dimensionale", "travi", "muri"):
            self._imposta(self.densita, materiale["densita"])

        if self._e_sovraccarico(materiale) or metodo == "fisso":
            self._imposta(self.peso_fisso, materiale["peso"], " kg/m²")

        if metodo == "profilo":
            self._imposta(self.peso_profilo, materiale["peso_lineare"])

        self.fonte_label.setText(materiale.get("fonte", "Non specificata"))
        self.calcola_peso()

    def aggiorna_etichette(self, metodo):
        """Adatta le diciture dei campi: travi oppure muri."""
        if metodo == "muri":
            testi = ("Spessore muro:", "Altezza muro:", "Muri - dato noto:",
                     "Muri - valore:", "Muri - equivalenza:")
            self.modo_interasse.setItemText(0, "Interasse (asse-asse)")
            self.modo_interasse.setItemText(1, "N. muri per metro")
        else:
            testi = ("Larghezza elemento (b):", "Altezza elemento (h):",
                     "Travi - dato noto:", "Travi - valore:",
                     "Travi - equivalenza:")
            self.modo_interasse.setItemText(0, "Interasse")
            self.modo_interasse.setItemText(1, "N. travi per metro")

        widget = (self.larghezza_elemento, self.altezza_elemento,
                  self.modo_interasse, self.valore_interasse,
                  self.info_travi)
        for w, t in zip(widget, testi):
            self.form.labelForField(w).setText(t)

        # il suffisso n. elementi/m dipende dal tipo
        if self.modo_interasse.currentIndex() == 1:
            suff = " muri/m" if metodo == "muri" else " travi/m"
            self.valore_interasse.setSuffix(suff)

    # -------------------------------------------------
    # TRAVI / MURI: INTERASSE <-> N. ELEMENTI AL METRO
    # -------------------------------------------------
    def cambia_modo_profilo(self):
        self.aggiorna_abilitazioni(self.get_materiale())
        self.calcola_peso()
    
    def cambia_modo_interasse(self):
        """Converte il valore mantenendo l'equivalenza fisica."""
        corrente = self.valore_interasse.value()

        if self.modo_interasse.currentIndex() == 0:
            # da n. travi/m -> interasse (cm)
            interasse_cm = 100.0 / corrente if corrente > 0 else 50.0
            self.valore_interasse.blockSignals(True)
            self.valore_interasse.setRange(1, 1000)
            self.valore_interasse.setDecimals(2)
            self.valore_interasse.setSuffix(" cm")
            self.valore_interasse.setValue(interasse_cm)
            self.valore_interasse.blockSignals(False)
        else:
            # da interasse (cm) -> n. travi/m
            n = 100.0 / corrente if corrente > 0 else 2.0
            self.valore_interasse.blockSignals(True)
            self.valore_interasse.setRange(0.1, 100)
            self.valore_interasse.setDecimals(3)
            self.valore_interasse.setSuffix(" travi/m")
            self.valore_interasse.setValue(n)
            self.valore_interasse.blockSignals(False)

        self.calcola_peso()

    def interasse_m(self):
        """Interasse delle travi in metri, qualunque sia il dato inserito."""
        v = self.valore_interasse.value()
        if v <= 0:
            return None
        if self.modo_interasse.currentIndex() == 0:
            return v / 100.0      # il valore è l'interasse in cm
        return 1.0 / v            # il valore è il numero di travi al metro

    # -------------------------------------------------
    # CALCOLO PESO
    # -------------------------------------------------

    def calcola_peso(self):

        materiale = self.get_materiale()
        if not materiale:
            return None

        metodo = materiale.get("metodo")

        if self._e_sovraccarico(materiale):
            # il database e il campo sono in kg/m²: converto in kN/m²
            valore = self.peso_fisso.value() * G / 1000
            unita = "kN/m²"

        elif metodo == "fisso":
            valore = self.peso_fisso.value()
            unita = "kg/m²"

        elif metodo == "densita":
            valore = self.densita.value() * self.spessore.value() / 100
            unita = "kg/m²"

        elif metodo in ("travi", "muri"):
            # kg/m² = densità * b * h / interasse
            # (travi: b = larghezza, h = altezza della sezione;
            #  muri:  b = spessore,  h = altezza del muro)
            interasse = self.interasse_m()
            if interasse is None:
                return None

            b = self.larghezza_elemento.value() / 100
            h = self.altezza_elemento.value() / 100

            valore = self.densita.value() * b * h / interasse
            unita = "kg/m²"

            kg_m = self.densita.value() * b * h   # peso al metro di elemento
            nome_el = "muri" if metodo == "muri" else "travi"
            self.info_travi.setText(
                f"interasse {interasse * 100:.1f} cm  =  "
                f"{1 / interasse:.2f} {nome_el}/m  -  "
                f"singolo elemento {kg_m:.1f} kg/m"
            )

        elif metodo == "dimensionale":
            # elemento lineare (es. cordolo): kg/m = densità * b * h * n
            b = self.larghezza_elemento.value() / 100
            h = self.altezza_elemento.value() / 100
            n = self.numero_elementi.value()

            valore = self.densita.value() * b * h * n
            unita = "kg/m"

        elif metodo == "profilo":
            p = self.peso_profilo.value()
            if self.modo_profilo.currentIndex() == 1:
                # profili ripetuti: kg/m² = peso al metro / interasse
                interasse = self.interasse_m()
                if interasse is None:
                    return None
                valore = p / interasse
                unita = "kg/m²"
                self.info_travi.setText(
                    f"interasse {interasse * 100:.1f} cm  =  "
                    f"{1 / interasse:.2f} profili/m  -  "
                    f"singolo profilo {p:.1f} kg/m"
                )
            else:
                valore = p * self.numero_elementi.value()
                unita = "kg/m"
                self.info_travi.setText("-")

        else:
            return None

        self.peso_label.setText(f"{valore:.2f} {unita}")
        return valore, unita

    # -------------------------------------------------
    # AGGIUNTA MATERIALE
    # -------------------------------------------------

    def aggiungi_materiale(self):

        risultato = self.calcola_peso()
        if risultato is None:
            QMessageBox.warning(
                self, "Attenzione", "Seleziona un materiale valido."
            )
            return

        valore, unita = risultato
        materiale = self.get_materiale()
        metodo = materiale.get("metodo")

        distribuito = (
            metodo == "profilo" and self.modo_profilo.currentIndex() == 1
        )

        categoria = self.categoria.currentText()
        nome = (
            f"{self.tipo.currentText()} - "
            f"{self.produttore.currentText()} - "
            f"{self.prodotto.currentText()}"
        )

        b = self.larghezza_elemento.value()
        h = self.altezza_elemento.value()

        if metodo in ("travi", "muri"):
            interasse_cm = self.interasse_m() * 100
            if metodo == "muri":
                dimensioni = (
                    f"sp. {b:.1f} cm x h {h:.1f} cm, "
                    f"interasse {interasse_cm:.1f} cm"
                )
            else:
                dimensioni = (
                    f"{b:.1f} x {h:.1f} cm, "
                    f"interasse {interasse_cm:.1f} cm"
                )
        elif metodo == "dimensionale":
            dimensioni = (
                f"{b:.1f} x {h:.1f} cm "
                f"(n. {int(self.numero_elementi.value())})"
            )
        elif metodo == "densita":
            dimensioni = f"{self.spessore.value():.2f} cm"

        elif metodo == "profilo":
            base = (
                f"{self.prodotto.currentText()} - "
                f"{self.peso_profilo.value():.2f} kg/m"
            )
            if distribuito:
                dimensioni = f"{base}, interasse {self.interasse_m() * 100:.1f} cm"
            else:
                dimensioni = f"{base} (n. {int(self.numero_elementi.value())})"
        else:
            dimensioni = "-"

        # Segnala se densità / peso sono stati modificati rispetto al database
        fonte = materiale.get("fonte", "Non specificata")
        modificato = False
        if metodo in ("densita", "dimensionale", "travi", "muri"):
            modificato = abs(self.densita.value() - materiale["densita"]) > 1e-9
        elif metodo == "fisso" or self._e_sovraccarico(materiale):
            modificato = abs(self.peso_fisso.value() - materiale["peso"]) > 1e-9
        elif metodo == "profilo":
            modificato = abs(self.peso_profilo.value() - materiale["peso_lineare"]) > 1e-9
        if modificato:
            fonte += " (valore modificato dall'utente)"

        riga = self.tabella.rowCount()
        self.tabella.insertRow(riga)

        valori = [categoria, nome, dimensioni, f"{valore:.2f}", unita, fonte]
        for colonna, dato in enumerate(valori):
            self.tabella.setItem(riga, colonna, QTableWidgetItem(str(dato)))

        if unita == "kg/m":
            tipo_calcolo = "lineare"
        elif unita == "kN/m²":
            tipo_calcolo = "sovraccarico"
        else:
            tipo_calcolo = "superficiale"

        # dati per il disegno schematico
        if tipo_calcolo == "sovraccarico":
            tipo_disegno, spessore_cm = "sovraccarico", 0.0
        elif metodo == "densita":
            tipo_disegno, spessore_cm = "continuo", self.spessore.value()
        elif metodo == "travi":
            tipo_disegno, spessore_cm = "travi", h
        elif metodo == "muri":
            tipo_disegno, spessore_cm = "muri", h
        elif metodo == "dimensionale":
            tipo_disegno, spessore_cm = "blocco", h
        elif metodo == "profilo":
            spessore_cm = materiale.get("h_cm", 20.0)
            tipo_disegno = "travi" if distribuito else "blocco"
        else:
            # peso fisso: spessore dal database se presente, altrimenti 2 cm
            tipo_disegno = "fisso"
            spessore_cm = materiale.get("spessore", 2.0)

        self.strati.append({
            "nome": nome,
            "etichetta": f"{categoria}: {self.prodotto.currentText()}",
            "categoria": categoria,
            "valore": valore,
            "unita": unita,
            "tipo_calcolo": tipo_calcolo,
            "tipo_disegno": tipo_disegno,
            "spessore_cm": spessore_cm,
            "dimensioni": dimensioni,
            "b_cm": materiale.get("b_cm", b) if metodo == "profilo" else b,
            "interasse_cm": (
                self.interasse_m() * 100
                if (metodo in ("travi", "muri") or distribuito) else 0
            ),
        })

        self.canvas.set_strati(self.strati)
        self.aggiorna_totali()

    # -------------------------------------------------
    # RIMOZIONE MATERIALE
    # -------------------------------------------------

    def rimuovi_materiale(self):
        riga = self.tabella.currentRow()
        if riga < 0:
            return

        self.tabella.removeRow(riga)
        self.strati.pop(riga)
        self.canvas.set_strati(self.strati)
        self.aggiorna_totali()

    # -------------------------------------------------
    # SOMMA DEI CARICHI
    # -------------------------------------------------

    def aggiorna_totali(self):

        totale_kg_m2 = 0.0
        totale_kg_m = 0.0
        totale_q_kn_m2 = 0.0

        for elemento in self.strati:
            valore = elemento["valore"]
            unita = elemento["unita"]

            if unita == "kg/m²":
                totale_kg_m2 += valore
            elif unita == "kg/m":
                totale_kg_m += valore
            elif unita == "kN/m²":
                totale_q_kn_m2 += valore

        larghezza = self.larghezza.value()

        g_superficiale = totale_kg_m2 * G / 1000          # kN/m²
        g_lineare = totale_kg_m * G / 1000                # kN/m

        carico_superficiale_lineare = g_superficiale * larghezza
        q_lineare = totale_q_kn_m2 * larghezza

        g_totale_lineare = carico_superficiale_lineare + g_lineare
        totale_lineare = g_totale_lineare + q_lineare

        self.totale_kg.setText(f"{totale_kg_m2:.2f} kg/m²")
        self.totale_kn.setText(f"{g_superficiale:.3f} kN/m²")
        self.carico_lineare.setText(f"{totale_lineare:.3f} kN/m")
        self.peso_lineare.setText(f"{totale_kg_m:.2f} kg/m")
        self.sovraccarico.setText(f"{totale_q_kn_m2:.2f} kN/m²")
        self.carico_permanente.setText(f"{g_totale_lineare:.3f} kN/m")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    finestra = LoadViewer()
    finestra.show()

    sys.exit(app.exec())