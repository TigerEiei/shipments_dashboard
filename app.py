
# ==========================================
# 1. นำเข้าไลบรารี
# ==========================================

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path


# ==========================================
# 2. ตั้งค่าหน้าเว็บไซต์
# ==========================================

st.set_page_config(
    page_title="Shipment Dashboard",
    page_icon="📦",
    layout="wide"
)


# ==========================================
# 3. ชื่อและคำอธิบายเว็บไซต์
# ==========================================

st.title("📦 แดชบอร์ดวิเคราะห์ข้อมูลการขนส่งสินค้า")

st.markdown("""
เว็บไซต์นี้จัดทำขึ้นเพื่อวิเคราะห์ประสิทธิภาพการขนส่งสินค้า
โดยใช้ข้อมูลจริงจากไฟล์ CSV

สามารถตรวจสอบจำนวนพัสดุ สถานะการจัดส่ง
ระยะเวลา และต้นทุนการขนส่งได้
""")

st.divider()


# ==========================================
# 4. อ่านข้อมูล CSV แบบ GZIP
# ==========================================

@st.cache_data
def load_data():

    # ค้นหาโฟลเดอร์เดียวกับ app.py
    base_dir = Path(__file__).resolve().parent

    # ไฟล์ข้อมูลอยู่ระดับเดียวกับ app.py
    file_path = base_dir / "shipments_clean_final.csv.gz"

    # ตรวจสอบว่ามีไฟล์หรือไม่
    if not file_path.is_file():
        raise FileNotFoundError(
            f"ไม่พบไฟล์ข้อมูล: {file_path}"
        )

    # อ่านไฟล์ GZIP
    df = pd.read_csv(
        file_path,
        compression="gzip"
    )

    # แปลงคอลัมน์วันที่
    date_columns = [
        "shipped_at",
        "promised_at",
        "delivered_at",
        "returned_at"
    ]

    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col],
                errors="coerce"
            )

    return df


# ==========================================
# 5. โหลดข้อมูลและตรวจสอบความถูกต้อง
# ==========================================

try:

    df = load_data()

except FileNotFoundError as e:

    st.error("ไม่พบไฟล์ข้อมูลที่เว็บไซต์ต้องใช้")

    st.code(str(e))

    st.info(
        "กรุณาตรวจสอบว่าไฟล์ "
        "shipments_clean_final.csv.gz "
        "อยู่ระดับเดียวกับ app.py บน GitHub"
    )

    st.stop()

except Exception as e:

    st.error("เกิดข้อผิดพลาดระหว่างอ่านไฟล์ข้อมูล")

    st.code(f"{type(e).__name__}: {e}")

    st.stop()


# ตรวจสอบคอลัมน์ที่จำเป็น
required_columns = [
    "shipment_id",
    "shipped_at",
    "promised_at",
    "delivered_at",
    "zone_id",
    "service_id",
    "carrier_id",
    "shipping_charge_baht",
    "status"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:

    st.error(
        f"ไม่พบคอลัมน์ที่จำเป็น: {missing_columns}"
    )

    st.stop()


# ตรวจสอบข้อมูลวันที่
if df["shipped_at"].isna().all():

    st.error("ไม่พบข้อมูลวันที่จัดส่งที่ใช้งานได้")

    st.stop()


# ==========================================
# 6. แถบด้านข้างสำหรับตัวกรองข้อมูล
# ==========================================

st.sidebar.header("🔎 ตัวกรองข้อมูล")

# ตัวกรองวันที่
date_data = df["shipped_at"].dropna()

min_date = date_data.min().date()
max_date = date_data.max().date()

selected_dates = st.sidebar.date_input(
    "เลือกช่วงวันที่จัดส่ง",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:

    start_date, end_date = selected_dates

else:

    start_date = selected_dates
    end_date = selected_dates


# ตัวกรองสถานะ
status_options = sorted(
    df["status"].dropna().unique().tolist()
)

selected_status = st.sidebar.multiselect(
    "สถานะการจัดส่ง",
    options=status_options,
    default=status_options
)


# ตัวกรองบริษัทขนส่ง
carrier_options = sorted(
    df["carrier_id"].dropna().unique().tolist()
)

selected_carriers = st.sidebar.multiselect(
    "บริษัทขนส่ง",
    options=carrier_options,
    default=carrier_options
)


# ตัวกรองพื้นที่
zone_options = sorted(
    df["zone_id"].dropna().unique().tolist()
)

selected_zones = st.sidebar.multiselect(
    "พื้นที่จัดส่ง",
    options=zone_options,
    default=zone_options
)


# ตัวกรองประเภทบริการ
service_options = sorted(
    df["service_id"].dropna().unique().tolist()
)

selected_services = st.sidebar.multiselect(
    "ประเภทบริการ",
    options=service_options,
    default=service_options
)


# ==========================================
# 7. กรองข้อมูลตามเงื่อนไข
# ==========================================

filtered_df = df.copy()

# กรองวันที่จัดส่ง
filtered_df = filtered_df[
    (filtered_df["shipped_at"].dt.date >= start_date) &
    (filtered_df["shipped_at"].dt.date <= end_date)
]

# กรองสถานะ
filtered_df = filtered_df[
    filtered_df["status"].isin(selected_status)
]

# กรองบริษัทขนส่ง
filtered_df = filtered_df[
    filtered_df["carrier_id"].isin(selected_carriers)
]

# กรองพื้นที่
filtered_df = filtered_df[
    filtered_df["zone_id"].isin(selected_zones)
]

# กรองประเภทบริการ
filtered_df = filtered_df[
    filtered_df["service_id"].isin(selected_services)
]


# ==========================================
# 8. ตรวจสอบข้อมูลหลังกรอง
# ==========================================

st.subheader("📊 ภาพรวมข้อมูล")

col_info1, col_info2 = st.columns(2)

col_info1.metric(
    "ข้อมูลทั้งหมด",
    f"{len(df):,} รายการ"
)

col_info2.metric(
    "ข้อมูลหลังกรอง",
    f"{len(filtered_df):,} รายการ"
)

if filtered_df.empty:

    st.warning(
        "ไม่พบข้อมูลตามเงื่อนไขที่เลือก "
        "กรุณาปรับตัวกรองใหม่"
    )

    st.stop()


# ==========================================
# 9. คำนวณ KPI
# ==========================================

total_shipments = len(filtered_df)

success_count = (
    filtered_df["status"] == "ส่งสำเร็จ"
).sum()

returned_count = (
    filtered_df["status"] == "ตีกลับ"
).sum()

lost_count = (
    filtered_df["status"] == "สูญหาย"
).sum()


success_rate = (
    success_count / total_shipments * 100
)

returned_rate = (
    returned_count / total_shipments * 100
)

lost_rate = (
    lost_count / total_shipments * 100
)


# ==========================================
# 10. คำนวณระยะเวลาจัดส่ง
# ==========================================

successful_df = filtered_df[
    (filtered_df["status"] == "ส่งสำเร็จ") &
    (filtered_df["delivered_at"].notna()) &
    (filtered_df["shipped_at"].notna())
].copy()

successful_df["delivery_hours"] = (
    successful_df["delivered_at"] -
    successful_df["shipped_at"]
).dt.total_seconds() / 3600


if not successful_df.empty:

    avg_delivery_hours = successful_df[
        "delivery_hours"
    ].mean()

else:

    avg_delivery_hours = 0


# ==========================================
# 11. คำนวณอัตราจัดส่งล่าช้า
# ==========================================

late_df = successful_df[
    successful_df["promised_at"].notna()
]

late_count = (
    late_df["delivered_at"] >
    late_df["promised_at"]
).sum()

late_rate = (
    late_count / len(late_df) * 100
    if len(late_df) > 0 else 0
)


# ==========================================
# 12. คำนวณค่าขนส่ง
# ==========================================

total_shipping_charge = (
    filtered_df["shipping_charge_baht"].sum()
)


# ==========================================
# 13. แสดง KPI Cards
# ==========================================

st.subheader("🎯 ตัวชี้วัดประสิทธิภาพการขนส่ง")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "📦 พัสดุทั้งหมด",
    f"{total_shipments:,} รายการ"
)

col2.metric(
    "✅ จัดส่งสำเร็จ",
    f"{success_count:,} รายการ"
)

col3.metric(
    "📈 อัตราจัดส่งสำเร็จ",
    f"{success_rate:.2f}%"
)

col4.metric(
    "↩️ พัสดุตีกลับ",
    f"{returned_count:,} รายการ"
)


col5, col6, col7, col8 = st.columns(4)

col5.metric(
    "❌ พัสดุสูญหาย",
    f"{lost_count:,} รายการ"
)

col6.metric(
    "⏰ อัตราจัดส่งล่าช้า",
    f"{late_rate:.2f}%"
)

col7.metric(
    "🕒 ระยะเวลาจัดส่งเฉลี่ย",
    f"{avg_delivery_hours:.2f} ชั่วโมง"
)

col8.metric(
    "💰 ค่าขนส่งรวม",
    f"{total_shipping_charge:,.2f} บาท"
)


st.divider()


# ==========================================
# 14. กราฟจำนวนพัสดุรายวัน
# ==========================================

st.subheader("📅 จำนวนพัสดุตามวันที่จัดส่ง")

daily_data = (
    filtered_df
    .dropna(subset=["shipped_at"])
    .assign(
        shipment_date=lambda x:
        x["shipped_at"].dt.date
    )
    .groupby("shipment_date")
    .size()
    .reset_index(name="จำนวนพัสดุ")
)

if not daily_data.empty:

    fig_daily = px.line(
        daily_data,
        x="shipment_date",
        y="จำนวนพัสดุ",
        markers=True,
        title="แนวโน้มจำนวนพัสดุรายวัน"
    )

    fig_daily.update_layout(
        xaxis_title="วันที่จัดส่ง",
        yaxis_title="จำนวนพัสดุ"
    )

    st.plotly_chart(
        fig_daily,
        use_container_width=True
    )


# ==========================================
# 15. กราฟสถานะพัสดุตามบริษัทขนส่ง
# ==========================================

st.subheader("🚚 สถานะพัสดุแยกตามบริษัทขนส่ง")

carrier_status = (
    filtered_df
    .groupby(["carrier_id", "status"])
    .size()
    .reset_index(name="จำนวนพัสดุ")
)

fig_carrier = px.bar(
    carrier_status,
    x="carrier_id",
    y="จำนวนพัสดุ",
    color="status",
    barmode="group",
    title="จำนวนพัสดุตามบริษัทขนส่งและสถานะ"
)

fig_carrier.update_layout(
    xaxis_title="บริษัทขนส่ง",
    yaxis_title="จำนวนพัสดุ",
    legend_title="สถานะ"
)

st.plotly_chart(
    fig_carrier,
    use_container_width=True
)


# ==========================================
# 16. กราฟค่าขนส่งแยกตามพื้นที่
# ==========================================

st.subheader("💰 ค่าขนส่งแยกตามพื้นที่")

zone_cost = (
    filtered_df
    .groupby("zone_id")["shipping_charge_baht"]
    .sum()
    .reset_index()
)

zone_cost.columns = [
    "พื้นที่",
    "ค่าขนส่งรวม"
]

fig_zone = px.bar(
    zone_cost,
    x="พื้นที่",
    y="ค่าขนส่งรวม",
    title="ค่าขนส่งรวมแยกตามพื้นที่",
    text_auto=".2s"
)

fig_zone.update_layout(
    xaxis_title="พื้นที่จัดส่ง",
    yaxis_title="ค่าขนส่ง (บาท)"
)

st.plotly_chart(
    fig_zone,
    use_container_width=True
)


# ==========================================
# 17. ตารางรายละเอียดข้อมูลพัสดุ
# ==========================================

st.subheader("📋 รายละเอียดข้อมูลพัสดุ")

st.write(
    f"แสดงข้อมูล 1,000 รายการแรก "
    f"จากทั้งหมด {len(filtered_df):,} รายการ"
)

st.dataframe(
    filtered_df.head(1000),
    use_container_width=True,
    hide_index=True
)


# ==========================================
# 18. ข้อควรระวังในการวิเคราะห์
# ==========================================

st.divider()

st.subheader("⚠️ ข้อควรระวังในการแปลผล")

st.markdown("""
- อัตราจัดส่งล่าช้าคำนวณเฉพาะพัสดุที่จัดส่งสำเร็จ
  และมีข้อมูลวันที่ส่งจริงกับวันที่กำหนดส่งครบถ้วน

- ระยะเวลาจัดส่งเฉลี่ยคำนวณเฉพาะพัสดุที่จัดส่งสำเร็จ
  และมีวันที่จัดส่งกับวันที่ส่งถึงครบถ้วน

- ค่าขนส่งรวมหมายถึงผลรวมของ
  `shipping_charge_baht`
  ไม่ใช่ต้นทุนการดำเนินงานทั้งหมด

- ข้อมูลการหยุดชะงักของการขนส่งมีค่าว่างจำนวนมาก
  จึงไม่ควรตีความว่าค่าว่างหมายถึงไม่มีเหตุขัดข้อง
""")

st.caption(
    "Shipment Dashboard | วิเคราะห์ข้อมูลการขนส่งจากข้อมูลจริง"
)
