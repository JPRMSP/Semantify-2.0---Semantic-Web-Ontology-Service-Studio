import streamlit as st
import re
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
from rdflib import Graph, Namespace, RDF, RDFS, URIRef
from io import BytesIO
import base64
import graphviz

st.set_page_config(page_title="Semantify 2.0 – Semantic Web Studio", layout="wide")

st.title("🌐 Semantify 2.0 – Semantic Web Ontology & Service Studio")
st.caption("Build ontologies, RDF graphs, OWL schemas, and semantic services – all in real-time!")

# ---------------- Sidebar -----------------
st.sidebar.header("⚙️ Controls")
st.sidebar.info("Use the tabs above to explore ontology building, graphs, queries, and more.")

# ---------------- Tabs --------------------
tabs = st.tabs(["🧠 Ontology Builder", "🌐 Graph Visualization", "🔍 Semantic Queries", "📦 Export & Merge", "🏗️ Semantic Web Layers"])

# ========== TAB 1: Ontology Builder ==========
with tabs[0]:
    st.header("🧠 Ontology Builder")
    st.markdown("Enter domain text to extract concepts, generate ontology, RDF triples, and OWL definitions.")

    user_text = st.text_area("✍️ Enter domain text:", 
        "Plants absorb sunlight through photosynthesis. Photosynthesis produces oxygen. Oxygen supports life.")

    generate_btn = st.button("🔎 Generate Ontology")

    if generate_btn and user_text.strip():
        sentences = re.split(r'[.?!]', user_text)
        concepts = set()
        relations = []

        for s in sentences:
            s = s.strip()
            if not s:
                continue
            words = re.findall(r'\b[A-Z]?[a-z]{3,}\b', s)
            for w in words:
                concepts.add(w.lower())
            parts = s.split()
            if len(parts) >= 3:
                subj = parts[0].capitalize()
                pred = " ".join(parts[1:-1])
                obj = parts[-1].capitalize()
                relations.append((subj, pred, obj))

        st.subheader("🌱 Extracted Concepts")
        st.success(", ".join(sorted(concepts)))

        # --- RDF Triple Generation ---
        st.subheader("🔗 RDF Triples")
        rdf_graph = Graph()
        ex = Namespace("http://example.org/")
        rdf_graph.bind("ex", ex)

        for subj, pred, obj in relations:
            subj_uri = URIRef(ex[subj])
            obj_uri = URIRef(ex[obj])
            rdf_graph.add((subj_uri, RDF.type, RDFS.Class))
            rdf_graph.add((obj_uri, RDF.type, RDFS.Class))
            rdf_graph.add((subj_uri, ex[pred.replace(" ", "_")], obj_uri))

        rdf_data = rdf_graph.serialize(format='turtle')
        st.code(rdf_data, language="turtle")

        # --- OWL Representation ---
        st.subheader("🦉 OWL Representation")
        owl_output = []
        for c in concepts:
            owl_output.append(f"Class: {c.capitalize()}")
        for subj, pred, obj in relations:
            owl_output.append(f"ObjectProperty: {pred.replace(' ', '_')}\n  Domain: {subj}\n  Range: {obj}")

        owl_text = "\n".join(owl_output)
        st.code(owl_text, language="owl")

        st.session_state['relations'] = relations
        st.session_state['concepts'] = concepts
        st.session_state['rdf'] = rdf_data
        st.session_state['owl'] = owl_text
    elif generate_btn:
        st.warning("⚠️ Please enter text before generating ontology.")

# ========== TAB 2: Graph Visualization ==========
with tabs[1]:
    st.header("🌐 Ontology Graph Visualization")
    if 'relations' in st.session_state:
        relations = st.session_state['relations']

        graph_choice = st.radio("📊 Choose Visualization Library", ["pyvis", "networkx", "graphviz"], horizontal=True)

        if graph_choice == "networkx":
            G = nx.DiGraph()
            for subj, pred, obj in relations:
                G.add_edge(subj, obj, label=pred)

            plt.figure(figsize=(8, 6))
            pos = nx.spring_layout(G)
            nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=2000, font_size=10, arrows=True)
            edge_labels = nx.get_edge_attributes(G, 'label')
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
            st.pyplot(plt)

        elif graph_choice == "pyvis":
            net = Network(height="600px", width="100%", directed=True)
            for subj, pred, obj in relations:
                net.add_node(subj, label=subj)
                net.add_node(obj, label=obj)
                net.add_edge(subj, obj, label=pred)

            net.save_graph("ontology_graph.html")
            html_file = open("ontology_graph.html", 'r', encoding='utf-8')
            html_content = html_file.read()
            st.components.v1.html(html_content, height=600, scrolling=True)

        elif graph_choice == "graphviz":
            dot = graphviz.Digraph()
            for subj, pred, obj in relations:
                dot.node(subj, subj)
                dot.node(obj, obj)
                dot.edge(subj, obj, label=pred)
            st.graphviz_chart(dot)
    else:
        st.warning("⚠️ Generate ontology first in Tab 1.")

# ========== TAB 3: Semantic Queries ==========
with tabs[2]:
    st.header("🔍 Semantic Query Engine")
    if 'relations' in st.session_state:
        query = st.text_input("Ask a SPARQL-like question (e.g., What does Plants relate to?)")
        if st.button("🔍 Run Query"):
            found = []
            for subj, pred, obj in st.session_state['relations']:
                if subj.lower() in query.lower() or obj.lower() in query.lower():
                    found.append(f"{subj} --[{pred}]--> {obj}")
            if found:
                st.success("✅ Query Results:")
                for r in found:
                    st.write("•", r)
            else:
                st.error("❌ No matching semantic relations found.")
    else:
        st.warning("⚠️ Generate ontology first in Tab 1.")

# ========== TAB 4: Export & Merge ==========
with tabs[3]:
    st.header("📦 Export Ontology Files & Merge")
    if 'rdf' in st.session_state and 'owl' in st.session_state:
        rdf_bytes = st.session_state['rdf'].encode('utf-8')
        owl_bytes = st.session_state['owl'].encode('utf-8')

        st.download_button("⬇️ Download RDF (.ttl)", data=rdf_bytes, file_name="ontology.ttl", mime="text/turtle")
        st.download_button("⬇️ Download OWL (.owl)", data=owl_bytes, file_name="ontology.owl", mime="application/rdf+xml")

        st.subheader("🔄 Ontology Merge")
        uploaded = st.file_uploader("Upload another RDF or OWL file to merge")
        if uploaded:
            new_graph = Graph()
            new_graph.parse(uploaded, format='turtle')
            merged = Graph()
            merged.parse(data=st.session_state['rdf'], format='turtle')
            for stmt in new_graph:
                merged.add(stmt)
            st.success("✅ Ontologies merged successfully!")
            st.code(merged.serialize(format='turtle'), language="turtle")
    else:
        st.warning("⚠️ Generate ontology first in Tab 1.")

# ========== TAB 5: Semantic Web Layers ==========
with tabs[4]:
    st.header("🏗️ Semantic Web Layered Architecture")
    st.markdown("""
    ### 🧬 Layered Structure of the Semantic Web
    - **XML Layer:** Base syntax for structured documents.
    - **RDF Layer:** Represents knowledge as subject-predicate-object triples.
    - **Ontology Layer (OWL):** Adds semantics and relationships to data.
    - **Logic Layer:** Enables reasoning and inference over ontologies.
    - **Proof Layer:** Provides explanation and justification of inferences.
    - **Trust Layer:** Ensures data reliability, provenance, and security.
    - **Application Layer:** Delivers user-facing services using semantic knowledge.
    """)
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Semantic_Web_Stack.svg/1024px-Semantic_Web_Stack.svg.png", caption="Semantic Web Stack Architecture", use_container_width=True)
