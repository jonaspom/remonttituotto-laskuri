import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

st.set_page_config(page_title="Taloyhtiön liikehuoneiston remontin tuottoanalyysi", layout="wide")

st.sidebar.title("Syötä parametrit")

alv = st.sidebar.number_input("ALV (%)", value=25.5, step=0.1)
remontin_hinta = st.sidebar.number_input("Remontin hinta (sis. ALV)", value=100000, step=1000)
laina_aika = st.sidebar.number_input("Laina-aika (vuotta)", value=10, step=1, min_value=1)
korkoprosentti = st.sidebar.number_input("Lainan korko (%)", value=10.0, step=0.1)
remontin_kesto = st.sidebar.number_input("Remontin kesto (kk)", value=6, step=1, min_value=0)
etsinnan_kesto = st.sidebar.number_input("Uuden vuokralaisen etsintä (kk)", value=6, step=1, min_value=0)
nykyinen_vuokra = st.sidebar.number_input("Nykyinen vuokra (alv 0, €/kk)", value=2100, step=100)
vuokran_korotus = st.sidebar.number_input("Vuokran korotus (%)", value=50.0, step=1.0)
vuosikulut = st.sidebar.number_input("Liikehuoneiston vuotuiset kulut (sis. ALV)", value=6000, step=100)
laskenta_vuodet = st.sidebar.number_input("Laskenta-aika (vuotta)", value=10, step=1, min_value=1)

remontin_alv = alv
vuokran_alv = alv
kulu_alv = alv

remontin_alv_osuus = remontin_hinta * remontin_alv / (100 + remontin_alv)
remontin_netto = remontin_hinta - remontin_alv_osuus
laina_maara = remontin_netto
uusi_vuokra = nykyinen_vuokra * (1 + vuokran_korotus / 100)

vuosituotot = []
vuosikorko = []
vuosilyhennykset = []
vuosilainanhoitomenot = []
jalki_laina = laina_maara
vuosilyhennys = laina_maara / laina_aika
kokonaiskassavirta = 0
kertyva_kassavirta = []
kertynyt = 0

for vuosi in range(1, laskenta_vuodet + 1):
    if vuosi == 1:
        kk_vuokratuloa = max(12 - remontin_kesto - etsinnan_kesto, 0)
    else:
        kk_vuokratuloa = 12

    vuokratulo = uusi_vuokra * kk_vuokratuloa
    vuokra_alv = vuokratulo * vuokran_alv / 100
    kulujen_alv_vahennys = vuosikulut * kulu_alv / (100 + kulu_alv)  # tämä on uusi hyöty

    korko = jalki_laina * korkoprosentti / 100 if vuosi <= laina_aika else 0
    lyhennys = vuosilyhennys if vuosi <= laina_aika else 0

    vuosilainanhoitomenot.append(korko + lyhennys)
    vuosikorko.append(korko)
    vuosilyhennykset.append(lyhennys)

    # HUOM: Kuluja ei enää vähennetä - vain uusi ALV-vähennys on lisättynä!
    vuosikassavirta = (
        vuokratulo
        + vuokra_alv
        + kulujen_alv_vahennys
        - lyhennys
        - korko
    )
    vuosituotot.append(vuosikassavirta)
    kokonaiskassavirta += vuosikassavirta
    kertynyt += vuosikassavirta
    kertyva_kassavirta.append(kertynyt)
    if vuosi <= laina_aika:
        jalki_laina -= vuosilyhennys

tappiot = nykyinen_vuokra * remontin_kesto + uusi_vuokra * etsinnan_kesto

maksuajan_takaisinmaksu_vuosi = None
for idx, kertynyt in enumerate(kertyva_kassavirta):
    if kertynyt - tappiot > 0 and maksuajan_takaisinmaksu_vuosi is None:
        maksuajan_takaisinmaksu_vuosi = idx + 1

# ---- ULKOASU ----

st.title("Taloyhtiön liikehuoneiston remontin tuottoanalyysi")
st.markdown("""
Tämä laskuri auttaa arvioimaan liiketilan remontin kannattavuutta taloyhtiölle. Syötä vasemmalla oleviin kenttiin taloyhtiön ja suunnitellun remontin tiedot. Tulokset ja graafit päivittyvät automaattisesti.
""")

st.header("Yhteenveto hankkeesta")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Perustiedot")
    st.markdown(f"""
- **Remontin kustannus (sis. ALV):** {remontin_hinta:,.2f} €
- **Remontin kesto:** {remontin_kesto} kk
- **Uuden vuokralaisen etsintä:** {etsinnan_kesto} kk
- **Vuokra ennen remonttia:** {nykyinen_vuokra:,.2f} €/kk (alv 0)
- **Vuokra remontin jälkeen:** {uusi_vuokra:,.2f} €/kk (alv 0, +{vuokran_korotus:.1f} %)
- **Vuokran ALV:** {vuokran_alv:.1f} %
- **Vuotuiset kulut:** {vuosikulut:,.2f} € (sis. ALV {kulu_alv:.1f} %)
- **Laina-aika:** {laina_aika} vuotta
- **Korko:** {korkoprosentti:.2f} %
""")

with col2:
    st.subheader("Laskennalliset arvot")
    st.markdown(f"""
- **Remontin ALV-vähennys:** {remontin_alv_osuus:,.2f} €
- **Remontin nettohinta (lainan määrä):** {remontin_netto:,.2f} €
- **Lainan vuosilyhennys:** {vuosilyhennys:,.2f} €
- **Liiketilan kulujen ALV-vähennys:** {vuosikulut * kulu_alv / (100 + kulu_alv):,.2f} € / vuosi
""")

st.info("""
**Huom!** Liikehuoneistoon kohdistuvien muiden kulujen ALV-vähennys muodostaa uuden kassavirtahyödyn vasta remontin ja uuden alv-velvollisen vuokralaisen jälkeen. Kulut itsessään eivät ole uusi tappio – vain ALV-vähennys kasvattaa tuottoa investoinnin jälkeen.
""")

st.header("Kassavirta- ja tuottoanalyysi")

st.markdown(f"""
- **Remontin ja vuokralaisen etsinnän aikana menetetty vuokratulo yhteensä:** {tappiot:,.2f} €
- **Ensimmäisen vuoden vuokratuloja saadaan vain {max(12 - remontin_kesto - etsinnan_kesto, 0)} kk:lta, minkä jälkeen täysi vuokratulo alkaa.**
- **Kokonaistuotto (eli kassavirta kaikkien kulujen ja menetysten jälkeen) {laskenta_vuodet} vuoden aikana:** {(kokonaiskassavirta - tappiot):,.2f} €
""")

if maksuajan_takaisinmaksu_vuosi:
    st.markdown(f"- **Investointi maksaa itsensä takaisin noin {maksuajan_takaisinmaksu_vuosi}. vuoden kohdalla (kertyvä kassavirta positiivinen).**")
else:
    st.markdown("- **Investointi ei maksa itseään takaisin laskenta-ajalla (kertyvä kassavirta jää negatiiviseksi).**")

with st.expander("Vuosittaiset lainanhoitomenot (lyhennys + korko)"):
    lainataulu = []
    for vuosi in range(laskenta_vuodet):
        lainataulu.append([
            f"Vuosi {vuosi+1}",
            f"{vuosilyhennykset[vuosi]:,.2f} €",
            f"{vuosikorko[vuosi]:,.2f} €",
            f"{vuosilainanhoitomenot[vuosi]:,.2f} €",
        ])
    st.table(
        pd.DataFrame(lainataulu, columns=["Vuosi", "Lyhennys", "Korko", "Yhteensä"])
    )

st.header("Vuosikohtaiset kassavirrat ja lainanhoitomenot")
datataulu = []
for vuosi in range(laskenta_vuodet):
    datataulu.append([
        f"Vuosi {vuosi+1}",
        vuosituotot[vuosi],
        vuosilainanhoitomenot[vuosi],
        kertyva_kassavirta[vuosi] - tappiot
    ])
st.table(
    pd.DataFrame(datataulu, columns=["Vuosi", "Kassavirta", "Lainanhoitomenot", "Kertyvä kassavirta (tappiot huomioiden)"])
)

# ---- VISUALISOINTI ----
st.header("Visualisointi")
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(np.arange(1, laskenta_vuodet + 1), vuosituotot, alpha=0.8, label="Vuosikassavirta")
ax.plot(np.arange(1, laskenta_vuodet + 1), kertyva_kassavirta, marker='o', color='black', label="Kertyvä kassavirta")
ax.axhline(0, color='grey', linestyle='--')
ax.set_title("Vuosikassavirrat ja kertyvä kassavirta")
ax.set_xlabel("Vuosi")
ax.set_ylabel("€")
ax.legend()
st.pyplot(fig)

with st.expander("Mahdollisia riskejä ja huomioita"):
    st.markdown("""
- Remontin mahdollinen viivästyminen kasvattaa vuokratulojen menetystä.
- Remontin kustannusarvion ylittyminen kasvattaa lainatarvetta ja vuosikuluja.
- Mikäli vuokraa ei saada korotettua suunnitellusti tai uusi vuokralainen viivästyy, tuotot heikkenevät.
- Korkotason nousu kasvattaa korkokuluja, jos korko ei ole kiinteä.
- Vuokratuottoihin ja kuluihin ei tässä mallissa ole sisällytetty vuosittaisia indeksikorotuksia tai inflaatiota.
    """)

st.caption("Tämä laskuri ei ole sijoitus- tai taloudellista neuvontaa, vaan antaa suuntaa-antavan arvion investoinnin vaikutuksesta taloyhtiön kassavirtaan.")
