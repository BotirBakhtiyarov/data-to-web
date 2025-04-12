import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI
import os
from dotenv import load_dotenv

# Atrof-muhit o‘zgaruvchilarini yuklash
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# DeepSeek API klientini ishga tushirish
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

# AI tahlilini oqim orqali amalga oshirish funksiyasi
def get_ai_analysis(data_description):
    """
    DeepSeek API orqali ma'lumotlar tavsifiga asoslangan AI tahlilini oqim sifatida oladi.

    Args:
        data_description (str): Ma'lumotlar to‘plamining statistik tavsifi.

    Yields:
        str: AI tomonidan yaratilgan tahlil qismlari.
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Siz ma'lumotlarni tahlil qilish bo‘yicha mutaxassissiz. Berilgan ma'lumotlar tavsifiga asoslanib, batafsil tahlil va amaliy tavsiyalar bering."},
                {"role": "user", "content": f"Ushbu ma'lumotlarni tahlil qiling va tushunchalar bering:\n{data_description}"},
            ],
            stream=True
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"AI tahlilida xato: {str(e)}"

# Streamlit ilovasini sozlash
st.set_page_config(page_title="Ma'lumotlardan Vebgacha", layout="wide", initial_sidebar_state="expanded")
st.title("Ma'lumotlardan Vebgacha: Interaktiv Ma'lumot Tahlili Vositas")
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
    Ushbu ilova kichik bizneslar, o‘qituvchilar va tadbirkorlar uchun mo‘ljallangan.  
    CSV yoki Excel faylingizni yuklang va AI yordamida tahlil va interaktiv dashboardni oching!
    """
)

# Fayl yuklovchi
uploaded_file = st.file_uploader("CSV yoki Excel faylini yuklang", type=["csv", "xlsx"], help="Qo‘llab-quvvatlanadigan formatlar: CSV, Excel (.xlsx)")

if uploaded_file is not None:
    # Yuklangan faylni o‘qish va qayta ishlash
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("Fayl muvaffaqiyatli yuklandi!")
        st.subheader("Yuklangan Ma'lumotlarning Oldindan Ko‘rinishi (Dastlabki 5 Qator)")
        st.dataframe(df.head(), use_container_width=True)

        # Asosiy statistik ma'lumotlar
        st.subheader("Ma'lumotlarning Statistik Xulosasi")
        st.write(df.describe())
    except Exception as e:
        st.error(f"Faylni o‘qishda xato: {str(e)}")
        st.stop()

    # Turli funksiyalar uchun yorliqlar
    tab1, tab2, tab3 = st.tabs(["AI Tahlili", "Vizualizatsiyalar", "Ma'lumotlarni Filtrlash"])

    # Yorliq 1: AI tahlili oqim bilan
    with tab1:
        st.subheader("AI Yordamida Tahlil va Tavsiyalar")
        data_description = df.describe().to_string()
        ai_insights = st.write_stream(get_ai_analysis(data_description))

    # Yorliq 2: Vizualizatsiyalar
    with tab2:
        st.subheader("Ma'lumot Vizualizatsiyalari")
        numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns

        if len(numeric_cols) >= 1:
            # Vizualizatsiya turini tanlash
            plot_type = st.selectbox(
                "Vizualizatsiya Turini Tanlang",
                ["Nuqtali", "Chiziqli", "Gistogramma", "Korrelyatsiya Matritsasi"],
                help="Ma'lumotlaringizni o‘rganish uchun vizualizatsiya tanlang."
            )

            if plot_type == "Nuqtali" and len(numeric_cols) >= 2:
                x_col = st.selectbox("X o‘qi ustunini tanlang", numeric_cols)
                y_col = st.selectbox("Y o‘qi ustunini tanlang", numeric_cols, index=1 if len(numeric_cols) > 1 else 0)
                fig = px.scatter(df, x=x_col, y=y_col, title=f"Nuqtali Grafik: {x_col} vs {y_col}")
                st.plotly_chart(fig, use_container_width=True)

            elif plot_type == "Chiziqli" and len(numeric_cols) >= 2:
                x_col = st.selectbox("X o‘qi ustunini tanlang", numeric_cols)
                y_col = st.selectbox("Y o‘qi ustunini tanlang", numeric_cols, index=1 if len(numeric_cols) > 1 else 0)
                fig = px.line(df, x=x_col, y=y_col, title=f"Chiziqli Grafik: {x_col} vs {y_col}")
                st.plotly_chart(fig, use_container_width=True)

            elif plot_type == "Gistogramma":
                x_col = st.selectbox("Gistogramma uchun ustunni tanlang", numeric_cols)
                fig = px.histogram(df, x=x_col, title=f"{x_col} Gistogrammasi")
                st.plotly_chart(fig, use_container_width=True)

            elif plot_type == "Korrelyatsiya Matritsasi":
                if not numeric_cols.empty:
                    corr = df[numeric_cols].corr()
                    fig = px.imshow(corr, title="Korrelyatsiya Matritsasi", color_continuous_scale="RdBu")
                    st.plotly_chart(fig, use_container_width=True)

            # Vizualizatsiyani HTML sifatida yuklab olish
            if plot_type != "Korrelyatsiya Matritsasi":
                fig.write_html("grafik.html")
                st.download_button(
                    label="Vizualizatsiyani HTML sifatida yuklab olish",
                    data=open("grafik.html", "rb").read(),
                    file_name=f"{plot_type.lower()}_grafik.html",
                    mime="text/html"
                )

    # Yorliq 3: Ma'lumotlarni filtrlash
    with tab3:
        st.subheader("Ma'lumotlaringizni Filtrlash")
        categorical_cols = df.select_dtypes(include=["object"]).columns

        if not categorical_cols.empty:
            st.sidebar.header("Filtrlash Imkoniyatlari")
            selected_col = st.sidebar.selectbox("Filtrlash uchun ustunni tanlang", categorical_cols)
            unique_values = df[selected_col].unique()
            selected_value = st.sidebar.selectbox(f"{selected_col} bo‘yicha filtrlang", unique_values)
            filtered_df = df[df[selected_col] == selected_value]

            st.write(f"Filtlangan Ma'lumotlar: {selected_col} = {selected_value}")
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.info("Filtrlash uchun kategorik ustunlar mavjud emas.")

    # HTMLga eksport qilish
    st.subheader("Natijalarni HTML sifatida Eksport Qilish")
    html_table = df.to_html(classes="table table-striped", index=False)
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
        <p>{ai_insights.replace('\n', '<br>')}</p>
    </body>
    </html>
    """

    st.download_button(
        label="To‘liq Dashboardni HTML sifatida Yuklab Olish",
        data=full_html.encode("utf-8"),
        file_name="ma'lumotlar_dashboard.html",
        mime="text/html"
    )

else:
    st.info("Iltimos, boshlash uchun fayl yuklang.")