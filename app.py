import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI
import os
from dotenv import load_dotenv

# Atrof-muhit o'zgaruvchilarini yuklash
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# DeepSeek API klientini boshlash
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

# AI tahlilini oqim bilan amalga oshirish funksiyasi
def get_ai_analysis(data_description):
    """
    DeepSeek API orqali ma'lumotlar tavsifiga asoslangan AI tahlilini oqim sifatida taqdim etadi.

    Args:
        data_description (str): Ma'lumotlar to'plamining statistik tavsifi.

    Yields:
        str: AI tahlilining bo'laklari.
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Siz ma'lumotlarni tahlil qilish bo'yicha mutaxassisiz. Taqdim etilgan ma'lumotlar tavsifiga asoslangan holda batafsil tahlil va amaliy tavsiyalar bering."},
                {"role": "user", "content": f"Ushbu ma'lumotlarni tahlil qiling va tushunchalar bering:\n{data_description}"},
            ],
            stream=True
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"AI tahlilida xatolik: {str(e)}"

# Streamlit ilovasini sozlash
st.set_page_config(page_title="Ma'lumotlardan Vebgacha", layout="wide", initial_sidebar_state="expanded")
st.title("Ma'lumotlardan Vebgacha: Interaktiv Ma'lumot Tahlili Vositalari")
st.markdown(
    """
    CSV yoki Excel faylini yuklang va avtomatlashtirilgan tahlil, interaktiv vizualizatsiyalar  
    va natijalarni HTML dashboard sifatida eksport qiling.
    """
)

# Yon panel: Ilova haqida ma'lumot
st.sidebar.header("Ushbu Vosita Haqida")
st.sidebar.markdown(
    """
    Ushbu ilova kichik bizneslar, o'qituvchilar va tadbirkorlar uchun mo'ljallangan.  
    CSV yoki Excel faylingizni yuklang va AI yordamida tahlil va interaktiv dashboard oching!
    """
)

# Fayl yuklovchi
uploaded_file = st.file_uploader("CSV yoki Excel faylini yuklang", type=["csv", "xlsx"], help="Qo'llab-quvvatlanadigan formatlar: CSV, Excel (.xlsx)")

if uploaded_file is not None:
    # Yuklangan faylni o'qish va qayta ishlash
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("Fayl muvaffaqiyatli yuklandi!")
        st.subheader("Yuklangan Ma'lumotlarning Oldindan Ko'rinishi (Birinchi 5 Qator)")
        st.dataframe(df.head(), use_container_width=True)

        # Asosiy statistikani ko'rsatish
        st.subheader("Ma'lumotlarning Umumiy Statistikas")
        st.write(df.describe())

        # Ma'lumotlar yuklanganda avtomatik AI tahlili
        st.subheader("Dastlabki AI Tahlili")
        data_description = df.describe().to_string()
        st.write_stream(get_ai_analysis(data_description))

    except Exception as e:
        st.error(f"Faylni o'qishda xatolik: {str(e)}")
        st.stop()

    # Turli funksiyalar uchun yorliqlar
    tab1, tab2, tab3 = st.tabs(["AI Tahlili", "Vizualizatsiyalar", "Ma'lumotlarni Filtrlash"])

    # Ma'lumotlar holatini saqlash
    if 'filtered_df' not in st.session_state:
        st.session_state.filtered_df = df.copy()

    # Tab 2: Vizualizatsiyalar
    with tab2:
        st.subheader("Ma'lumotlar Vizualizatsiyasi")
        numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns

        if len(numeric_cols) >= 1:
            # Vizualizatsiya turini tanlash
            plot_type = st.selectbox(
                "Vizualizatsiya Turini Tanlang",
                ["Nuqtali", "Chiziqli", "Gistogramma", "Korrelatsiya Matritsasi"],
                help="Ma'lumotlaringizni o'rganish uchun vizualizatsiyani tanlang."
            )

            if plot_type == "Nuqtali" and len(numeric_cols) >= 2:
                x_col = st.selectbox("X o'qi ustunini tanlang", numeric_cols)
                y_col = st.selectbox("Y o'qi ustunini tanlang", numeric_cols, index=1 if len(numeric_cols) > 1 else 0)
                fig = px.scatter(st.session_state.filtered_df, x=x_col, y=y_col, title=f"Nuqtali Grafik: {x_col} vs {y_col}")
                st.plotly_chart(fig, use_container_width=True)

            elif plot_type == "Chiziqli" and len(numeric_cols) >= 2:
                x_col = st.selectbox("X o'qi ustunini tanlang", numeric_cols)
                y_col = st.selectbox("Y o'qi ustunini tanlang", numeric_cols, index=1 if len(numeric_cols) > 1 else 0)
                fig = px.line(st.session_state.filtered_df, x=x_col, y=y_col, title=f"Chiziqli Grafik: {x_col} vs {y_col}")
                st.plotly_chart(fig, use_container_width=True)

            elif plot_type == "Gistogramma":
                x_col = st.selectbox("Gistogramma uchun ustunni tanlang", numeric_cols)
                fig = px.histogram(st.session_state.filtered_df, x=x_col, title=f"{x_col} Gistogrammasi")
                st.plotly_chart(fig, use_container_width=True)

            elif plot_type == "Korrelatsiya Matritsasi":
                if not numeric_cols.empty:
                    corr = st.session_state.filtered_df[numeric_cols].corr()
                    fig = px.imshow(corr, title="Korrelatsiya Matritsasi", color_continuous_scale="RdBu")
                    st.plotly_chart(fig, use_container_width=True)

            # Vizualizatsiyani HTML sifatida yuklab olish
            if plot_type != "Korrelatsiya Matritsasi":
                fig.write_html("plot.html")
                st.download_button(
                    label="Vizualizatsiyani HTML sifatida yuklab olish",
                    data=open("plot.html", "rb").read(),
                    file_name=f"{plot_type.lower()}_grafik.html",
                    mime="text/html"
                )

    # Tab 3: Ma'lumotlarni Filtrlash
    with tab3:
        st.subheader("Ma'lumotlarni Filtrlash")
        categorical_cols = df.select_dtypes(include=["object"]).columns

        if not categorical_cols.empty:
            st.sidebar.header("Filtrlash Imkoniyatlari")
            selected_col = st.sidebar.selectbox("Filtrlash uchun ustunni tanlang", categorical_cols)
            unique_values = df[selected_col].unique()
            selected_value = st.sidebar.selectbox(f"{selected_col} bo'yicha filtr", unique_values)
            st.session_state.filtered_df = df[df[selected_col] == selected_value]

            st.write(f"Filtlangan Ma'lumotlar: {selected_col} = {selected_value}")
            st.dataframe(st.session_state.filtered_df, use_container_width=True)
        else:
            st.info("Filtrlash uchun kategorik ustunlar mavjud emas.")

    # Tab 1: AI Tahlili (O'zgartirilgan ma'lumotlar uchun)
    with tab1:
        st.subheader("O'zgartirilgan Ma'lumotlar uchun AI Tahlili")
        if st.button("AI Xulosasini Olish"):
            data_description = st.session_state.filtered_df.describe().to_string()
            ai_insights = st.write_stream(get_ai_analysis(data_description))
        else:
            st.info("Vizualizatsiya yoki filtrlashdan so'ng AI tahlilini olish uchun 'AI Xulosasini Olish' tugmasini bosing.")

    # HTML ga eksport qilish
    st.subheader("Natijalarni HTML sifatida Eksport Qilish")
    html_table = st.session_state.filtered_df.to_html(classes="table table-striped", index=False)
    full_html = f"""
    <html>
    <head>
        <title>Ma'lumotlardan Vebgacha Natijalari</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #333; }}
            .table {{ border-collapse: collapse; width: 100%; }}
            .table th, .table td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            .table th {{ background-color: #f5f5f5; }}
            .table-striped tr:nth-child(even) {{ background-color: #f9f9f9; }}
        </style>
    </head>
    <body>
        <h1>Ma'lumotlardan Vebgacha Natijalari</h1>
        <h2>Yuklangan Ma'lumotlar</h2>
        {html_table}
        <h2>AI Tahlili</h2>
        <p>{"AI tahlili hali amalga oshirilmagan."}</p>
    </body>
    </html>
    """

    st.download_button(
        label="To'liq Dashboardni HTML sifatida Yuklab Olish",
        data=full_html.encode("utf-8"),
        file_name="ma'lumotlar_dashboard.html",
        mime="text/html"
    )

else:
    st.info("Boshlash uchun fayl yuklang.")