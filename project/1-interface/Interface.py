 
import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
import sys
import codecs
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid import AgGrid
from st_aggrid import GridUpdateMode
from PIL import Image
from collections import Counter

sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)

st.set_page_config(
    page_title="Automatic DVC",
    layout="wide"
)
st.title("Installation Analysis Subsea")

tooltip_css = """
<style>
    .tooltip {
      position: relative;
      display: inline-block;
      border-bottom: 1px dotted black;
      font-size: 15px;
      color: #FFFF00;
      cursor: pointer;
    }
    .tooltip .tooltip_text {
      visibility: hidden;
      width: 300px;
      background-color: black;
      color: #fff;
      text-align: center;
      border-radius: 6px;
      padding: 5px;
      position: absolute;
      z-index: 1;
      bottom: 125%;
      left: 50%;
      margin-left: -100px;
      opacity: 0;
      transition: opacity 0.3s;
    }
    .tooltip:hover .tooltip_text {
      visibility: visible;
      opacity: 1;
    }
</style>
"""

st.markdown(tooltip_css, unsafe_allow_html=True)
this_path = os.path.dirname(os.path.abspath(__file__))
image1_path = Image.open(this_path + "\\image\\Screenshot_1.jpg")
image2_path = Image.open(this_path + "\\image\\Screenshot_2.jpg")
image3_path = Image.open(this_path + "\\image\\Screenshot_3.jpg")
image4_path = Image.open(this_path + "\\image\\Screenshot_4.jpg")

def show_table(dict_data: pd.DataFrame, config: dict):
    """
    Shows the table in the interface
    :param dict_data: dict_data
    :param config: configuration of the table
    :return: configured table
    """
    return AgGrid(
        dict_data,
        gridOptions=config,
        editable=True,
        fit_columns_on_grid_load=True,
        height=250,
        width='100%',
        update_mode=GridUpdateMode.MODEL_CHANGED
    )

def data_treatment(data_: dict):
    """
    Receives data and treats it
    :param data_: grid_response_data
    :return: treated dataframe
    """
    df = pd.DataFrame(data_)
    df = df.map(lambda x: x.replace(",", ".") if isinstance(x, str) else x)
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
    for col in df.columns: 
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.replace("", pd.NA, inplace=True)
    df = df.dropna(how="all")
    df.reset_index(drop=True, inplace=True)
    return df

def creating_table(dict_data: pd.DataFrame, column_1: str, column_2: str) -> dict:
    """
    Creates the table configuration
    :param dict_data: dict to configure
    :param column_1: header_1 name
    :param column_2: header_2 name
    :return: grid_build of the table
    """
    gb = GridOptionsBuilder.from_dataframe(dict_data)
    gb.configure_default_column(editable=True, min_column_width=100, resizable=True)
    gb.configure_column(column_1, flex=1)
    gb.configure_column(column_2, flex=1)
    gb.configure_grid_options()
    g_build = gb.build()
    return g_build

def buoys_set(name_vessel: str):
    """
    Returns the vessel's buoy
    :param name_vessel: operation's vessel
    :return: set of vessel's buoys
    """
    set_of_buoys = "buoy_" + name_vessel.lower() + ".json"
    path = this_path + "\\buoy\\" + set_of_buoys
    with open(path, 'r', encoding='utf-8') as file:
        json_buoys = json.load(file)
        counter = list(Counter(json_buoys).items())
        quantity = [counter[i][1]
                    for i in range(len(counter))]
        buoy = [counter[i][0]
                for i in range(len(counter))]
        vessel_buoys_set = pd.DataFrame({
            "Quantity": quantity,
            "Buoy [kg]": buoy
        })
        return vessel_buoys_set

def st_number_input(label: str):
    """
    Pattern for st.number_input in this application
    :param label: Label for a unique st.number_input
    :return: st.number_input
    """
    return st.number_input(
        label=label, 
        value=.0, 
        min_value=-200.0, 
        max_value=1_000_000.0, 
        step=.01
        )

def st_image_input(path: Image, caption: str):
    """
    Pattern for 'st.image' in this application
    :param path: image's path
    :param caption: image's caption
    :return: 'st.image'
    """
    return st.image(
        path, 
        caption=caption, 
        use_column_width=False, 
        width=500
        )

data1 = pd.DataFrame(
    {
    'Curvature [1/m]': [pd.NA] * 50,
    'Bend Moment [N.m]': [pd.NA] * 50
    })

grid_options1 = creating_table(
    data1,
    "Curvature [1/m]",
    "Bend Moment [N.m]"
    )

data2 = pd.DataFrame(
    {
    'Distance from flange [m]': [pd.NA] * 50,
    'Flange Height to the seabed [mm]': [pd.NA] * 50
    })

grid_options2 = creating_table(
    data2,
    "Distance from flange [m]",
    "Flange Height to the seabed [mm]"
    )

data3 = pd.DataFrame(
    {
    'Position [m]': [pd.NA] * 50,
    'Buoyancy [kg]': [pd.NA] * 50
    })

grid_options3 = creating_table(
    data3,
    "Position [m]",
    "Buoyancy [kg]"
    )

tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Notes",
    "Flexible pipe",
    "Bend Restrictor",
    "End-Fitting",
    "Flange Adapter",
    "VCM",
    "Analysis",
    "Review"
])

with tab0:
    st.header("ADOPTED DATA")
    st.write(
        "ET-3000.00-1500-951-PMU-001 Rev. F - Basic requirements for the "
        "installation of VCMs"
    )
    st.write(
        "ET-3000.00-1500-941-PMU-006 Rev. C - Methodology and guidelines for "
        "load analysis in VCM"
    )
    col1, col2, col3 = st.columns([1.25, 1.25, 2])
    with col1:
        st.text(
            "SEABED DATA\n"
            "Longitudinal friction coefficient = 0.35\n"
            "Transversal friction coefficient = 0.9\n"
            "Normal stiffness = 100 kN/m/m\n"
            "Shear stiffness = 10000 kN/m/m\n"
            "Slope = 0.00 °\n"
            "Note: The friction coefficients are properties that\n"
            "depend not only on the soil but also on the pipe.\n\n"
        )
        st.text(
            "STEEL PROPERTIES\n"
            "Elastic Modulus = 2,07 . 10e8 kN/m²\n"
            "Poisson's Ratio = 0,3\n\n"
        )
        st.text(
            "DENSITIES\n"
            "Seawater: 1025 kg/m³\n"
            "Steel: 7800 kg/m³\n"
        )
    with col2:
        st.text(
            "BEND RESTRICTOR STIFFNESS\n"
            "Axial Stiffness: 10 kN\n"
            "Torsional Stiffness: 10 kN.m²\n\n"
        )
        st.text(
            "LINK OBJECTS\n"
            "Length: 3 m\n"
            "Axial stiffness: 1000 kN\n\n"
        )
        st.text(
            "CRANE CABLE\n"
            "OD = 0,09\n"
            "ID = 0\n"
            "W = 31 kgf/m\n"
            "Bending stiffness (EI) = 50 kN.m²\n"
            "Axial stiffness (EA) = 500.000 kN\n"
            "Torsional stiffness (GJ) = 200 kN.m²\n"
            "Poisson's ratio = 0,3\n"
        )
    with col3:
        st.write("")


with tab1:
    st.header("Flexible Pipe")
    st.write("Inform the Flexible Pipe's Data")
    col1, col2, col3, col4 = st.columns([1, 1, 2, 3])
    with col1:
        ident_line = st.text_input("1. Structure Number")
        water_depth = st_number_input("2. Water Depth [m]")
        st.markdown(
            '<div class="tooltip"># Lines length Tooltip'
            '<span class="tooltip_text">'
                "Filled just in case of jumper DVC.<br>"
                "(When line's length < Water depth)"
            '</span>'
            '</div>',
            unsafe_allow_html=True
        )
        line_length = st_number_input("3. Line's length [m]")
        contact_diameter_line = st_number_input("4. Contact Diameter [mm]")
        nominal_diameter_line = st_number_input('5. Nominal Diameter ["]')
        mbr_storage_line = st_number_input("6. MBR Storage [m]")
        mbr_installation_line = st_number_input("7. MBR Installation [m]")
        st.markdown(
            '<div class="tooltip"># Axial Stiffness Tooltip'
            '<span class="tooltip_text">'
                "Axial Stiffness considered for<br>"
                "a 100kN axial load"
            '</span>'
            '</div>',
            unsafe_allow_html=True
        )
        axial_stiffness_line = st_number_input("8. Axial Stiffness [kN]")
    with col2:
        wt_air_line = st_number_input("9. Wt, Empty in Air [kg/m]")
        sw_filled_air_line = st_number_input("10. S/W, Filled in Air [kg/m]")
        air_filled_sw_line = st_number_input("11. Air Filled in S/W [kg/m]")
        sw_filled_sw_line = st_number_input("12. S/W Filled in S/W [kg/m]")
        bending_stiffness_line = st_number_input("13. Pipe Bending Stiffness [kN.m²]")
        st.markdown(
            '<div class="tooltip"># Torsional Stiffness Tooltip'
            '<span class="tooltip_text">'
                "For cases in which there is no<br>"
                "Torsional Stiffness in datasheet,<br>"
                "use the values below:<br>"
                'ND=2,5" - TS=300kN.m²<br>'
                'ND=4" - TS=500kN.m²<br>'
                'ND=6"(no isolation) - TS=1000kN.m²<br>'
                'ND=6"(isolation) - TS=1500kN.m²<br>'
                'ND=8" - TS=2000kN.m²<br>'
                'ND=9,13" - TS=2300kN.m²<br>'
            '</span>'
            '</div>',
            unsafe_allow_html=True
        )
        torsional_stiffness_line = st_number_input("14. Torsional Stiffness (Limp Direction) [kN.m²]")
        st.markdown(
            '<div class="tooltip"># Rel. Elong. Tooltip'
            '<span class="tooltip_text">'
                "Just fill it if there is no Axial<br>"
                "Stiffness in datasheet."
            '</span>'
            '</div>',
            unsafe_allow_html=True
        )
        rel_elong_line = st_number_input("15. Rel. Elong. (%) for 100kN")
    with col3:
        st.header("Line's Stiffness Curve")
        grid_response1 = show_table(data1, grid_options1)
    with col4:
        if st.button("Generate Chart"):
            stiffness_curve_line = data_treatment(grid_response1["data"])
            with st.spinner("Processing... Please, wait!"):
                fig = px.scatter(
                    stiffness_curve_line,
                    x='Curvature [1/m]',
                    y='Bend Moment [N.m]',
                    title="Curvature x Bend Moment"
                )
                fig.update_traces(mode='lines+markers')
                st.plotly_chart(fig)

with tab2:
    st.header("Bend Restrictor")
    st.write("Inform the Bend Restrictor's Data")
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])
    with col1:
        type_bend_restrictor = st.radio("16. Material Selection", ["Steel", "Polymer"])
        ident_bend_restrictor = st.text_input("17. Structure Number")
        version_bend_restrictor = st.text_input("18. Document Version")
        if type_bend_restrictor == "Polymer":
            st.markdown(
                '<div class="tooltip"># Free Length Tooltip'
                '<span class="tooltip_text">'
                "Use Bend Restrictor's Free Length<br>"
                "less the Rigid Zone"
                '</span>'
                '</div>',
                unsafe_allow_html=True
            )
        length_bend_restrictor = st_number_input("19. Free Length [mm]")
        wt_air_bend_restrictor = st_number_input("20. Wt in Air [kg]")
        if type_bend_restrictor != "Polymer":
            st.markdown(
                '<div class="tooltip"># Wt in S/W Tooltip'
                '<span class="tooltip_text">'
                "If not informed, use (0,87 . Wt in Air)<br>"
                '</span>'
                '</div>',
                unsafe_allow_html=True
            )
        wt_sw_bend_restrictor = st_number_input("21. Wt in S/W [kg]")
    with col2:
        od_bend_restrictor = st_number_input("22. Outside Diameter [mm]")
        id_bend_restrictor = st_number_input("23. Internal Diameter [mm]")
        contact_diameter_bend_restrictor = st_number_input("24. Contact Diameter [mm]")
        locking_mbr_bend_restrictor = st_number_input("25. Locking MBR [m]")
        bend_moment_bend_restrictor = st_number_input("26. Maximum Allowable Bend Moment [kN.m]")
        shear_stress_bend_restrictor = st_number_input("27. Maximum Allowable Shear Stress [kN]")
    if type_bend_restrictor == "Polymer":
        with col3:
            rz_ident_bend_restrictor = st.text_input("28. RZ Structure Number")
            rz_version_bend_restrictor = st.text_input("29. RZ Document Version")
            rz_wt_air_bend_restrictor = st_number_input("30. RZ Wt in Air [kg]")
            st.markdown(
                '<div class="tooltip">Wt in S/W Tooltip'
                '<span class="tooltip_text">'
                "If not informed, use (0,87 . Wt in Air)<br>"
                '</span>'
                '</div>',
                unsafe_allow_html=True
            )
            rz_wt_sw_bend_restrictor = st_number_input("31. RZ Wt in S/W [kg]")
        with col4:
            rz_length_bend_restrictor = st_number_input("32. RZ Total Length [mm]")
            rz_od_bend_restrictor = st_number_input("33. RZ Outside Diameter [mm]")
            rz_id_bend_restrictor = st_number_input("34. RZ Internal Diameter [mm]")
            rz_contact_diameter_bend_restrictor = st_number_input("35. RZ Contact Diameter [mm]")
        with col5:
            image_bend_restrictor = st_image_input(image1_path, "Typical Bend Restrictor, with MBR")
    else:
        with col3:
            image_bend_restrictor = st_image_input(image1_path, "Typical Bend Restrictor, with MBR")

with tab3:
    st.header("End-Fitting")
    st.write("Inform the End-Fitting's Data")
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        ident_end_fitting = st.text_input("36. Structure Number")
        version_end_fitting = st.text_input("37. Document Version")
        wt_air_end_fitting = st_number_input("38. Wt in Air [kg]")
        st.markdown(
            '<div class="tooltip">Wt in S/W Tooltip'
            '<span class="tooltip_text">'
            "If not informed, use (0,87 . Wt in Air)<br>"
            '</span>'
            '</div>',
            unsafe_allow_html=True
        )
        wt_sw_end_fitting = st_number_input("39. Wt in S/W [kg]")
    with col2:
        length_end_fitting = st_number_input("40. Total Length [mm]")
        od_end_fitting = st_number_input("41. Outside Diameter [mm]")
        id_end_fitting = st_number_input("42. Internal Diameter [mm]")
        contact_diameter_end_fitting = st_number_input("43. Contact Diameter [mm]")
    with col3:
        image_end_fitting = st_image_input(image2_path, "Typical End Fitting")

with tab4:
    st.header("Flange Adapter")
    st.write("Inform the Flange Adapter's Data")
    col1, col2 = st.columns(2)
    with col1:
        ident_flange = st.text_input("44. Structure Number")
        version_flange = st.text_input("45. Document Version")
        wt_air_flange = st_number_input("46. Wt in Air [kg]")
        st.markdown(
            '<div class="tooltip">Wt in S/W Tooltip'
            '<span class="tooltip_text">'
            "If not informed, use (0,87 . Wt in Air)<br>"
            '</span>'
            '</div>',
            unsafe_allow_html=True
        )
        wt_sw_flange = st_number_input("47. Wt in S/W [kg]")
    with col2:
        length_flange = st_number_input("48. Total Length [mm]")
        od_flange = st_number_input("49. Outside Diameter [mm]")
        id_flange = st_number_input("50. Internal Diameter [mm]")
        contact_diameter_flange = st_number_input("51. Contact Diameter [mm]")


with tab5:
    st.header("VCM")
    st.write("Inform the VCM's Data")
    col1, col2, col3, col4 = st.columns([1, 1.5, 2.5, 2])
    with col1:
        subsea_equipment = st.text_input("52. Subsea Equipment")
        version_vcm = st.text_input("53. Document Version")
        supplier_vcm = st.text_input("54. VCM's Supplier Identification")
        drawing_vcm = st.text_input("55. VCM's Drawing Number")
        subsea_equipment_type = st.text_input("56. Specify the Connection")
        wt_sw_vcm = st_number_input("57. Weight in S/W")
        declination = st_number_input("58. Declination Goose-neck's Angle")
    with col2:
        a_vcm = st_number_input("59. A [mm] - VCM Flange's Vertical Distance to the Seabed")
        b_vcm = st_number_input("60. B [mm] - Handle's Vertical Distance to the Flange")
        c_vcm = st_number_input("61. C [mm] - Handle's Horizontal Distance to the Flange")
        d_vcm = st_number_input("62. D [mm] - CoG Vertical Distance to the Flange")
        e_vcm = st_number_input("63. E [mm] - CoG Horizontal Distance to the Flange")
        f_vcm = st_number_input("64. F [mm] - VCM Base's Vertical Distance to the Flange")
        g_vcm = st_number_input("65. G [mm] - VCM Base's Horizontal Distance to the Flange")
        h_vcm = st_number_input("66. H [mm] - CoG Position Relative to the y-Axis")
    with col3:
        image_vcm = st_image_input(image3_path, "Typical VCM")
    with col4:
        st.header("Bathymetric Data")
        grid_response2 = show_table(data2, grid_options2)
        image_bathymetric = st_image_input(image4_path, "Seabed Bathymetric")

with tab6:
    st.header("Analysis Data")
    st.write("Inform the Vessel, the Report's Buoy Configuration "
             "and the Structural Limits for this Analysis")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        rt_number = st.text_input("RT+Number")
        vessel = st.selectbox("67. Vessel", ["CDA", "SKA", "SKB", "SKN", "SKR", "SKO", "SKV"])
        if vessel:
            data4 = buoys_set(vessel)
            grid_options4 = creating_table(data4, "Quantity", "Buoy [kg]")
            grid_response4 = show_table(data4, grid_options4)
    with col2:
        st.write("Report's Buoy Configuration")
        grid_response3 = show_table(data3, grid_options3)
    with col3:
        st.write("DVC 1st - VCM in Hub with hanging line (Cas2 3i.A)")
        traction_3ia = st_number_input("68. Traction [kN]")
        shear_3ia = st_number_input("69. Shear [kN]")
        bend_moment_3ia = st_number_input("70. Bend Moment [kN.m]")
    with col4:
        st.write("DVC 1st - VCM in Hub with hanging line (Cas2 3i.B)")
        traction_3ib = st_number_input("71. Traction [kN]")
        shear_3ib = st_number_input("72. Shear [kN]")
        bend_moment_3ib = st_number_input("73. Bend Moment [kN.m]")
    with col5:
        st.write("DVC 1st - VCM in Hub (Cas2 3ii)")
        traction_3ii = st_number_input("74. Traction [kN]")
        shear_3ii = st_number_input("75. Shear [kN]")
        bend_moment_3ii = st_number_input("76. Bend Moment [kN.m]")


with tab7:
    uploaded_file = st.file_uploader("Choose the file", type=["json"])
    if uploaded_file is not None:
        file_content = uploaded_file.read()
        data = json.loads(file_content)
        dict_linha = data[0]
        stiffness_curve = data[1]
        dict_vertebra = data[2]
        dict_conector = data[3]
        dict_flange = data[4]
        dict_mcv = data[5]
        bathymetric = data[6]
        rt = data[7]
        vessel_id = data[8]
        set_buoy = data[9]
        config_buoy = data[10]
        struct_limit = data[11]
    if st.button("Run Application"):
        with st.spinner("Processing... Please, wait!"):
            col7_1, col7_2, col7_3, col7_4, col7_5, col7_6 = st.columns(6)
            with col7_1:
                st.write("Line's data")
                if line_length == .0:
                    line_length = water_depth
                dict_line = {
                    'ident_line': ident_line,
                    'line_length': line_length,
                    'wt_air_line': wt_air_line,
                    'sw_filled_air_line': sw_filled_air_line,
                    'air_filled_sw_line': air_filled_sw_line,
                    'sw_filled_sw_line': sw_filled_sw_line,
                    'water_depth': water_depth,
                    'contact_diameter_line': contact_diameter_line,
                    'nominal_diameter_line': nominal_diameter_line,
                    'mbr_storage_line [m]': mbr_storage_line,
                    'mbr_installation_line': mbr_installation_line,
                    'bending_stiffness_line': bending_stiffness_line,
                    'torsional_stiffness_line':torsional_stiffness_line,
                    'axial_stiffness_line': axial_stiffness_line,
                    'rel_elong_line': rel_elong_line
                }
                dict_line_dataframe = st.dataframe(dict_line)
                st.write("Line's Stiffness Data")
                dict_stiffness = data_treatment(grid_response1["data"])
                data1_dataframe = st.dataframe(dict_stiffness)
            with col7_2:
                st.write("Bend Restrictor's Data")
                dict_bend_restrictor = {
                    'ident_bend_restrictor': ident_bend_restrictor,
                    'version_bend_restrictor': version_bend_restrictor,
                    'type_bend_restrictor': type_bend_restrictor,
                    'length_bend_restrictor': length_bend_restrictor,
                    'wt_air_bend_restrictor': wt_air_bend_restrictor,
                    'wt_sw_bend_restrictor': wt_sw_bend_restrictor,
                    'od_bend_restrictor': od_bend_restrictor,
                    'id_bend_restrictor': id_bend_restrictor,
                    'contact_diameter_bend_restrictor': contact_diameter_bend_restrictor,
                    'locking_mbr_bend_restrictor': locking_mbr_bend_restrictor,
                    'bend_moment_bend_restrictor': bend_moment_bend_restrictor,
                    'shear_stress_bend_restrictor': shear_stress_bend_restrictor
                }
                dict_bend_restrictor_dataframe = st.dataframe( dict_bend_restrictor)
                if type_bend_restrictor == "Polymer":
                    st.write("Rigid Zone's Bend Restrictor's Data")
                    dict_rz_bend_restrictor = {
                        'rz_ident_bend_restrictor': rz_ident_bend_restrictor,
                        'rz_version_bend_restrictor': rz_version_bend_restrictor,
                        'rz_length_bend_restrictor': rz_length_bend_restrictor,
                        'rz_wt_air_bend_restrictor': rz_wt_air_bend_restrictor,
                        'rz_wt_sw_bend_restrictor': rz_wt_sw_bend_restrictor,
                        'rz_od_bend_restrictor': rz_od_bend_restrictor,
                        'rz_id_bend_restrictor': rz_id_bend_restrictor,
                        'rz_contact_diameter_bend_restrictor': rz_contact_diameter_bend_restrictor
                    }
                    dict_rz_dataframe = st.dataframe(dict_rz_bend_restrictor)
                    dict_bend_restrictor.update(dict_rz_bend_restrictor)
            with col7_3:
                st.write("End Fitting's Data")
                dict_end_fitting = {
                    'ident_end_fitting': ident_end_fitting,
                    'version_end_fitting': version_end_fitting,
                    'wt_air_end_fitting': wt_air_end_fitting,
                    'wt_sw_end_fitting': wt_sw_end_fitting,
                    'length_end_fitting': length_end_fitting,
                    'od_end_fitting': od_end_fitting,
                    'id_end_fitting': id_end_fitting,
                    'contact_diameter_end_fitting':
                        contact_diameter_end_fitting
                }
                dict_end_fitting_dataframe = st.dataframe(dict_end_fitting)
                st.write("Flange Adapter's Data")
                dict_flange = {
                    'ident_flange': ident_flange,
                    'version_flange': version_flange,
                    'wt_air_flange': wt_air_flange,
                    'wt_sw_flange': wt_sw_flange,
                    'length_flange': length_flange,
                    'od_flange': od_flange,
                    'id_flange': id_flange,
                    'contact_diameter_flange': contact_diameter_flange
                }
                dict_flange_dataframe = st.dataframe(dict_flange)
            with col7_4:
                st.write("VMC's Data")
                dict_vcm = {
                    'subsea_equipment': subsea_equipment,
                    'version_vcm': version_vcm,
                    'supplier_vcm': supplier_vcm,
                    'drawing_vcm': drawing_vcm,
                    'subsea_equipment_type': subsea_equipment_type,
                    'wt_sw_vcm': wt_sw_vcm,
                    'declination': declination,
                    'a_vcm': a_vcm,
                    'b_vcm': b_vcm,
                    'c_vcm': c_vcm,
                    'd_vcm': d_vcm,
                    'e_vcm': e_vcm,
                    'f_vcm': f_vcm,
                    'g_vcm': g_vcm,
                    'h_vcm': h_vcm
                }
                dict_vcm_dataframe = st.dataframe(dict_vcm)
                st.write("Bathymetric Data")
                dict_bathymetric = data_treatment(grid_response2["data"])
                data2_dataframe = st.dataframe(dict_bathymetric)
            with col7_5:
                vessel_name = vessel
                vessel_str = st.write(f"Vessel: {vessel_name}")
                st.write("Set of Buoys")
                buoy_set = data_treatment(grid_response4["data"])
                data4_dataframe = st.dataframe(buoy_set)
            with col7_6:
                st.write("Report's Buoys Configuration")
                buoys_configuration = data_treatment(grid_response3["data"])
                data3_dataframe = st.dataframe(buoys_configuration)
                st.write("Report's Structural Limits")
                structural_limits = {
                    "3ia": [traction_3ia, shear_3ia, bend_moment_3ia],
                    "3ib": [traction_3ib, shear_3ib, bend_moment_3ib],
                    "3ii": [traction_3ii, shear_3ii, bend_moment_3ii]
                }
                dict_strength_dataframe = st.dataframe(structural_limits)
        combined_data = (
            dict_line,  # 0
            [
                dict_stiffness["Curvature [1/m]"].tolist(),
                dict_stiffness["Bend Moment [N.m]"].tolist()
            ],  # 1
            dict_bend_restrictor,  # 2
            dict_end_fitting,  # 3
            dict_flange,  # 4
            dict_vcm,  # 5
            [
                dict_bathymetric["Distance from flange [m]"].tolist(),
                dict_bathymetric["Flange Height to the seabed [mm]"].tolist()
            ],  # 6
            rt_number,  # 7
            vessel,  # 8
            [
                buoy_set["Quantity"].tolist(),
                buoy_set["Buoy [kg]"].tolist()
            ],  # 9
            [
                buoys_configuration["Position [m]"].tolist(),
                buoys_configuration["Buoyancy [kg]"].tolist()
            ],  # 10
            structural_limits  # 11
        )
        json_data = json.dumps(combined_data, indent=4, ensure_ascii=False)
        st.download_button(
            label="Download JSON data",
            data=json_data,
            file_name=f"{rt_number}.json",
            mime="application/json"
        )
