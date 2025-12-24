"""Componentes UI reutilizáveis."""
import streamlit as st


def custom_css():
    """Aplica CSS customizado para mobile-first."""
    st.markdown("""
        <style>
        /* Mobile-first: Base styles */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            padding-left: 1rem;
            padding-right: 1rem;
            max-width: 100%;
        }

        /* Desktop: centraliza e limita largura */
        @media (min-width: 1024px) {
            .main .block-container {
                max-width: 1400px;
                margin: 0 auto;
                padding-left: 2rem;
                padding-right: 2rem;
            }
        }

        /* Cards */
        .custom-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 1rem;
            border: 1px solid #f0f0f0;
        }

        .custom-card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
            transition: all 0.3s ease;
        }

        /* Métricas customizadas */
        .metric-card {
            background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
            color: white;
            border-radius: 12px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 12px rgba(220, 38, 38, 0.25);
        }

        .metric-card h3 {
            font-size: 0.875rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            opacity: 0.9;
        }

        .metric-card .value {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .metric-card .label {
            font-size: 0.75rem;
            opacity: 0.8;
        }

        /* Badges */
        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-right: 0.5rem;
        }

        .badge-success {
            background: #d4edda;
            color: #155724;
        }

        .badge-warning {
            background: #fff3cd;
            color: #856404;
        }

        .badge-danger {
            background: #f8d7da;
            color: #721c24;
        }

        .badge-info {
            background: #d1ecf1;
            color: #0c5460;
        }

        /* Botões customizados */
        .stButton > button {
            border-radius: 8px;
            font-weight: 600;
            border: none;
            padding: 0.5rem 1.5rem;
            transition: all 0.3s ease;
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }

        /* Sidebar mobile */
        @media (max-width: 768px) {
            .css-1d391kg {
                padding-top: 1rem;
            }

            .main .block-container {
                padding-left: 0.5rem;
                padding-right: 0.5rem;
            }
        }

        /* Desktop: largura máxima confortável */
        @media (min-width: 768px) {
            .main .block-container {
                max-width: 1200px;
                margin: 0 auto;
            }
        }

        /* Títulos */
        h1 {
            font-weight: 700;
            margin-bottom: 1.5rem;
        }

        h2 {
            font-weight: 600;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }

        /* Forms */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select {
            border-radius: 8px;
            border: 2px solid #e0e0e0;
        }

        .stTextInput > div > div > input:focus,
        .stSelectbox > div > div > select:focus {
            border-color: #dc2626;
            box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.1);
        }

        /* Grid responsivo para desktop */
        @media (min-width: 768px) {
            .metric-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1rem;
            }
        }
        </style>
    """, unsafe_allow_html=True)


def metric_card(title: str, value: str, icon: str = "📊", color: str = "default"):
    """Card de métrica estilizado."""
    colors = {
        "default": "linear-gradient(135deg, #dc2626 0%, #991b1b 100%)",
        "success": "linear-gradient(135deg, #16a34a 0%, #15803d 100%)",
        "warning": "linear-gradient(135deg, #ea580c 0%, #c2410c 100%)",
        "info": "linear-gradient(135deg, #0284c7 0%, #0369a1 100%)",
    }

    gradient = colors.get(color, colors["default"])

    st.markdown(f"""
        <div class="metric-card" style="background: {gradient};">
            <h3>{icon} {title}</h3>
            <div class="value">{value}</div>
        </div>
    """, unsafe_allow_html=True)


def card(content: str, title: str = None):
    """Card simples com conteúdo."""
    title_html = f"<h3 style='margin-top: 0;'>{title}</h3>" if title else ""
    st.markdown(f"""
        <div class="custom-card">
            {title_html}
            {content}
        </div>
    """, unsafe_allow_html=True)


def badge(text: str, type: str = "info"):
    """Badge colorido."""
    return f'<span class="badge badge-{type}">{text}</span>'


def empty_state(icon: str, title: str, description: str, action_text: str = None):
    """Estado vazio com ícone e texto."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
            <div style="text-align: center; padding: 3rem 0;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">{icon}</div>
                <h3 style="margin-bottom: 0.5rem; color: #333;">{title}</h3>
                <p style="color: #666; margin-bottom: 1.5rem;">{description}</p>
            </div>
        """, unsafe_allow_html=True)

        if action_text:
            st.button(action_text, use_container_width=True, type="primary")


def section_header(title: str, subtitle: str = None):
    """Cabeçalho de seção."""
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)
    st.markdown("---")


def stat_grid(stats: list):
    """Grid de estatísticas."""
    cols = st.columns(len(stats))
    for col, stat in zip(cols, stats):
        with col:
            metric_card(
                title=stat.get("title"),
                value=stat.get("value"),
                icon=stat.get("icon", "📊"),
                color=stat.get("color", "default")
            )
