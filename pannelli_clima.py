"""Pannelli di input per i calcoli di neve e vento (NTC 2018)."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGroupBox, QGridLayout, QLabel, QComboBox, QDoubleSpinBox
)

import azioni_climatiche as ac


def _spin(minimo, massimo, decimali, valore, suffisso=""):
    s = QDoubleSpinBox()
    s.setRange(minimo, massimo)
    s.setDecimals(decimali)
    s.setValue(valore)
    if suffisso:
        s.setSuffix(suffisso)
    return s


class _PannelloBase(QGroupBox):
    """Griglia a 2 coppie etichetta/campo per riga + etichetta informativa."""

    cambiato = Signal()

    def __init__(self, titolo):
        super().__init__(titolo)
        self._griglia = QGridLayout(self)
        self._r = 0
        self._c = 0
        self._etichette = {}
        self.info = QLabel("")
        self.info.setWordWrap(True)
        self.info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

    def _aggiungi(self, testo, widget, intera_riga=False):
        if intera_riga and self._c != 0:
            self._c = 0
            self._r += 1
        etichetta = QLabel(testo)
        self._etichette[widget] = etichetta
        self._griglia.addWidget(etichetta, self._r, self._c * 2)
        self._griglia.addWidget(widget, self._r, self._c * 2 + 1)
        if isinstance(widget, QComboBox):
            widget.currentIndexChanged.connect(self.cambiato)
        else:
            widget.valueChanged.connect(self.cambiato)
        if intera_riga:
            self._c = 0
            self._r += 1
        else:
            self._c += 1
            if self._c == 2:
                self._c = 0
                self._r += 1

    def _chiudi(self):
        if self._c != 0:
            self._c = 0
            self._r += 1
        self._griglia.addWidget(self.info, self._r, 0, 1, 4)
        self._griglia.setColumnStretch(1, 1)
        self._griglia.setColumnStretch(3, 1)

    def _abilita(self, widget, attivo):
        widget.setEnabled(attivo)
        self._etichette[widget].setEnabled(attivo)


# =====================================================================
class PannelloNeve(_PannelloBase):

    def __init__(self):
        super().__init__("Parametri azione della neve (NTC 2018 par. 3.4)")

        self.quota = _spin(0, 3000, 1, 100, " m")
        self.zona = QComboBox()
        for i, (nome, province) in enumerate(ac.PROVINCE_NEVE.items()):
            self.zona.addItem(nome)
            self.zona.setItemData(i, province, Qt.ItemDataRole.ToolTipRole)
        self.topografia = QComboBox()
        self.topografia.addItems(ac.CLASSI_TOPOGRAFIA.keys())
        self.topografia.setCurrentText("Normale")
        self.ct = _spin(0.01, 2, 2, 1.0)
        self.alfa1 = _spin(0, 90, 1, 20, " °")
        self.alfa2 = _spin(0, 90, 1, 20, " °")
        self.barriera = QComboBox()
        self.barriera.addItems(["No", "Sì"])
        self.barriera.setToolTip(
            "Se l'estremità più bassa della falda termina con parapetto, barriera "
            "o altre costruzioni, μ non può essere assunto inferiore a 0,8.")

        self._aggiungi("as (altitudine s.l.m.):", self.quota)
        self._aggiungi("Zona:", self.zona)
        self._aggiungi("Classe di topografia (CE):", self.topografia)
        self._aggiungi("Coefficiente termico Ct:", self.ct)
        self._aggiungi("Inclinazione falda α1:", self.alfa1)
        self._aggiungi("Inclinazione falda α2:", self.alfa2)
        self._aggiungi("Presenza di barriera:", self.barriera)
        self._chiudi()

    def imposta_voce(self, voce):
        self._abilita(self.alfa2, voce.get("schema") != "una" or voce.get("forma") == "mu2")
        self._abilita(self.barriera, voce.get("forma") == "mu1")

    def parametri(self):
        return {
            "quota": self.quota.value(),
            "zona": self.zona.currentText(),
            "topografia": self.topografia.currentText(),
            "ct": self.ct.value(),
            "alfa1": self.alfa1.value(),
            "alfa2": self.alfa2.value(),
            "barriera": self.barriera.currentIndex() == 1,
        }

    def calcola(self, voce):
        try:
            r = ac.calcola_neve(self.parametri(), voce)
        except (ValueError, KeyError) as e:
            self.info.setText(f"⚠ {e}")
            return None
        self.info.setText(r["info"])
        return r


# =====================================================================
class PannelloVento(_PannelloBase):

    def __init__(self):
        super().__init__("Parametri azione del vento (NTC 2018 par. 3.3)")

        self.zona = QComboBox()
        self.zona.addItems(ac.ZONE_VENTO.keys())
        self.zona.setCurrentIndex(0)
        self.rugosita = QComboBox()
        for i, (lettera, testo) in enumerate(ac.RUGOSITA.items()):
            self.rugosita.addItem(lettera)
            self.rugosita.setItemData(i, testo, Qt.ItemDataRole.ToolTipRole)
        self.rugosita.setCurrentText("C")
        self.quota = _spin(0, 3000, 1, 100, " m")
        self.distanza = _spin(-200, 1000, 1, 10, " km")
        self.distanza.setToolTip("Distanza dalla costa: valore NEGATIVO se la costruzione è in mare.")
        self.TR = _spin(5, 2000, 0, 50, " anni")
        self.cd = _spin(0.5, 2, 2, 1.0)
        self.cd.setToolTip("Coefficiente dinamico: cautelativamente 1 per edifici regolari "
                           "non eccedenti 80 m e capannoni.")

        self.topografia = QComboBox()
        self.topografia.addItems(ac.TOPOGRAFIE)
        self.rilievo_H = _spin(0.1, 5000, 1, 250, " m")
        self.rilievo_D = _spin(0.1, 10000, 1, 30, " m")
        self.rilievo_h = _spin(0.1, 5000, 1, 10, " m")
        self.rilievo_x = _spin(0, 5000, 1, 10, " m")

        self.tipologia = QComboBox()
        self.tipologia.addItems(ac.TIPOLOGIE_VENTO)
        self.tipologia.setCurrentIndex(3)
        self.config = QComboBox()
        self.config.addItems(ac.CONFIGURAZIONI_VENTO)
        self.h_colmo = _spin(0.1, 200, 2, 6.5, " m")
        self.h_gronda = _spin(0, 200, 2, 4.0, " m")
        self.alfa = _spin(0, 90, 1, 30, " °")
        self.alfa.setToolTip("Inclinazione della falda sopravento. Se colmo = gronda la "
                             "copertura è piana e si usa α = 2° come nel foglio Excel.")
        self.copertura_multipla = QComboBox()
        self.copertura_multipla.addItems(ac.COPERTURE_MULTIPLE)
        self.superficie = QComboBox()
        self.superficie.addItems(ac.SUPERFICI.keys())
        self.superficie.setCurrentIndex(1)

        self._aggiungi("Zona:", self.zona, intera_riga=True)
        self._aggiungi("Classe di rugosità:", self.rugosita)
        self._aggiungi("as (altitudine s.l.m.):", self.quota)
        self._aggiungi("Distanza dalla costa:", self.distanza)
        self._aggiungi("TR (tempo di ritorno):", self.TR)
        self._aggiungi("Coefficiente dinamico cd:", self.cd)
        self._aggiungi("Topografia:", self.topografia, intera_riga=True)
        self._aggiungi("Rilievo - H:", self.rilievo_H)
        self._aggiungi("Rilievo - D:", self.rilievo_D)
        self._aggiungi("Rilievo - h:", self.rilievo_h)
        self._aggiungi("Rilievo - x:", self.rilievo_x)
        self._aggiungi("Tipologia costruzione:", self.tipologia, intera_riga=True)
        self._aggiungi("Configurazione cpi:", self.config)
        self._aggiungi("Coperture multiple:", self.copertura_multipla)
        self._aggiungi("H di colmo:", self.h_colmo)
        self._aggiungi("H di gronda:", self.h_gronda)
        self._aggiungi("Inclinazione falda sopravento α:", self.alfa)
        self._aggiungi("Superficie (tangenziale):", self.superficie)
        self._chiudi()

        self.topografia.currentIndexChanged.connect(self._abilitazioni_interne)
        self.tipologia.currentIndexChanged.connect(self._abilitazioni_interne)
        self._voce = {}
        self._abilitazioni_interne()

    def _abilitazioni_interne(self):
        rilievo = self.topografia.currentIndex() != 0
        for w in (self.rilievo_H, self.rilievo_D, self.rilievo_h):
            self._abilita(w, rilievo)
        self._abilita(self.rilievo_x, self.topografia.currentIndex() == 2)
        self._abilita(self.copertura_multipla, self.tipologia.currentIndex() == 4)
        tangenziale = self._voce.get("elemento") == "tangenziale"
        self._abilita(self.superficie, tangenziale)
        for w in (self.tipologia, self.config, self.alfa):
            self._abilita(w, not tangenziale)

    def imposta_voce(self, voce):
        self._voce = voce
        self._abilitazioni_interne()

    def parametri(self):
        return {
            "zona": self.zona.currentText(),
            "rugosita": self.rugosita.currentText(),
            "quota": self.quota.value(),
            "distanza": self.distanza.value(),
            "TR": self.TR.value(),
            "cd": self.cd.value(),
            "topografia": self.topografia.currentText(),
            "H": self.rilievo_H.value(),
            "D": self.rilievo_D.value(),
            "h": self.rilievo_h.value(),
            "x": self.rilievo_x.value(),
            "tipologia": self.tipologia.currentIndex(),
            "config": self.config.currentIndex(),
            "h_colmo": self.h_colmo.value(),
            "h_gronda": self.h_gronda.value(),
            "alfa": self.alfa.value(),
            "copertura_multipla": self.copertura_multipla.currentIndex(),
            "superficie": self.superficie.currentText(),
        }

    def calcola(self, voce):
        try:
            r = ac.calcola_vento(self.parametri(), voce)
        except (ValueError, KeyError) as e:
            self.info.setText(f"⚠ {e}")
            return None
        self.info.setText(r["info"])
        return r