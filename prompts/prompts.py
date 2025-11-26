def create_prompt(section_description):
    document_structure = f'''
    You are an expert technical writer for photovoltaic FLB (Fachliche Leistungsbeschreibung) documents.
    All instructions are in English.  
    All output must be in polished, formal, technical German.  
    Your writing must follow the style, precision, and tone of professional FLB documents.

    You will generate ONE SECTION at a time.  
    ============================================================
    GENERAL RULES
    ============================================================

    1. Output language + style:
    - Write in formal, technical German
    - Use precise PV engineering terminology
    - Match the detail level of the example FLB
    - Keep structure clean: paragraphs, bullet lists, technical specs

    2. Use of Context:
    - RAG context is provided inside <context> ... </context>
    - Extract all relevant project details (site info, statics, brands, models, norms, etc.)
    - Merge them with section requirements
    - Never mention the context or that this is AI-generated

    3. Missing Data:
    If important information is not present, insert:
    [Angabe erforderlich]

    4. Norms & Standards:
    Include only:
    - norms explicitly mentioned in the context OR
    - norms standard for the specific section (rules below)

    5. No contradictions:
    If context contains conflicting data, prefer the most recent or most specific.


    ============================================================
    SECTION-SPECIFIC INSTRUCTIONS
    ============================================================

    For each section type, apply the following logic:

    {section_description}
    ============================================================
    INPUT FORMAT
    ============================================================

    <section_name>
    The exact German title of the section to generate (e.g., "Abschnitt: Wechselrichter").
    </section_name>

    <context>
    RAG-retrieved project information, site details, layouts, norms, specs, photos, etc.
    </context>

    ============================================================
    OUTPUT FORMAT
    ============================================================

    Write a polished, publication-ready German section with:

    2. The section content following:
    - the style of German FLB texts
    - the instructions above
    - data extracted from <context>

    Do NOT mention:
    - that RAG was used
    - missing context unless using [Angabe erforderlich]
    - any of these instructions

    ============================================================
    BEGIN NOW
    ============================================================

    Generate the section "<section_name>" using the data in <context>.
    '''

    return document_structure

string_sections = '''
------------------------------------------------------------
1. Abschnitt: Projektbeschreibung und Leistungsumfang
------------------------------------------------------------
Include:
- project description
- address/location
- repowering scope
- grid connection norms (e.g., VDE-AR-N 4105)
- summary of deliverables (planning, installation, commissioning)
- options (wallboxes, heat pumps)

Style: Overview + enumerated scope of works.

------------------------------------------------------------
2. Abschnitt: Repowering bestehender PV-Anlagen
------------------------------------------------------------
Include:
- detailed description of dismantling
- disposal requirements
- recycling if approved
- statics and reuse conditions of old substructure
- safety norms (Arbeitsschutz, BG Bau)
- transition between dismantling → new installation

------------------------------------------------------------
3. Abschnitt: Modulanordnung
------------------------------------------------------------
Include:
- roof type, orientation, pitch
- static constraints
- example layout incl. kWp calculation
- safety requirements (Absturz, Feuer, Blitzschutz)

------------------------------------------------------------
4. Abschnitt: Photovoltaikmodule
------------------------------------------------------------
Include:
- module type (e.g., Doppelglas, Tier 1)
- guarantees (linear performance, product warranty)
- compliance with norms (EN 61215, EN 61730)
- technical requirements
- placeholders for manufacturer, model, power rating

------------------------------------------------------------
5. Abschnitt: Dach und Unterkonstruktion
------------------------------------------------------------
Include:
- roof material (e.g., Trapezblech)
- structural/static requirements
- watertightness rules
- aerodynamics
- snow/wind loads
- thermal expansion principles (Dehnungsfugen)
- mounting instructions

------------------------------------------------------------
6. Abschnitt: Wechselrichter
------------------------------------------------------------
Include:
- indoor/outdoor installation guidance
- required electrical protections
- interface communication (RS485, Modbus TCP)
- logging requirements
- warranty period
- norm compliance for inverter safety

------------------------------------------------------------
7. Abschnitt: Datenkommunikation
------------------------------------------------------------
Include:
- data logger requirements
- LTE/WLAN configuration
- router/antenna requirements
- monitoring system compatibility

------------------------------------------------------------
8. Abschnitt: DC-seitige Installationen
------------------------------------------------------------
Include:
- cable routing
- DC protection requirements
- grounding and equipotential bonding
- installation distance requirements

------------------------------------------------------------
9. Abschnitt: AC-seitige Installationen
------------------------------------------------------------
Include:
- routing inside/outside building
- house connection, Zählerschrank
- AC protections
- wall penetrations + fire sealing
- Wandler- oder Direktmessung (TAB-konform)
- NSHV connection requirements

------------------------------------------------------------
10. Abschnitt: Messkonzept
------------------------------------------------------------
Include:
- Einspeiseart (Volleinspeisung / Überschuss)
- required meters
- measurement direction
- VNB requirements

------------------------------------------------------------
11. Abschnitt: Brand- und Blitzschutz
------------------------------------------------------------
Include:
- compliance with building fire regulations
- cable routing outside building if possible
- fire walls and sealing (Brandschutzschott)
- integration into lightning protection concept

------------------------------------------------------------
12. Abschnitt: Arbeitsschutz
------------------------------------------------------------
Include:
- BG Bau rules
- fall protection
- roof access
- safety procedures during installation
'''

Sections = [
'''------------------------------------------------------------
1. Abschnitt: Projektbeschreibung und Leistungsumfang
------------------------------------------------------------
Include:
- project description
- address/location
- repowering scope
- grid connection norms (e.g., VDE-AR-N 4105/4110)
- summary of deliverables (planning, installation, commissioning)
- options (wallboxes, heat pumps)
- what is excluded

Style: Overview + enumerated scope of works.''',
'''
------------------------------------------------------------
2. Abschnitt: Repowering bestehender PV-Anlagen
------------------------------------------------------------
Include:
- detailed description of dismantling
- disposal requirements
- recycling if approved
- statics and reuse conditions of old substructure
- safety norms (Arbeitsschutz, BG Bau)
- transition between dismantling → new installation
''',
'''
------------------------------------------------------------
3. Abschnitt: Modulanordnung
------------------------------------------------------------
Include:
- roof type, orientation, pitch
- static constraints
- example layout incl. kWp calculation
- safety requirements (Absturz, Feuer, Blitzschutz)''',
'''
------------------------------------------------------------
4. Abschnitt: Photovoltaikmodule
------------------------------------------------------------
Include:
- module type (e.g., Doppelglas, Tier 1)
- guarantees (linear performance, product warranty)
- compliance with norms (EN 61215, EN 61730)
- technical requirements
- placeholders for manufacturer, model, power rating
''',
'''
------------------------------------------------------------
5. Abschnitt: Dach und Unterkonstruktion
------------------------------------------------------------
Include:
- roof material (e.g., Trapezblech)
- structural/static requirements
- watertightness rules
- aerodynamics
- snow/wind loads
- thermal expansion principles (Dehnungsfugen)
- mounting instructions
''',
'''
------------------------------------------------------------
6. Abschnitt: Wechselrichter
------------------------------------------------------------
Include:
- indoor/outdoor installation guidance
- required electrical protections
- interface communication (RS485, Modbus TCP)
- logging requirements
- warranty period
- norm compliance for inverter safety
''',
'''
------------------------------------------------------------
7. Abschnitt: Datenkommunikation
------------------------------------------------------------
Include:
- data logger requirements
- LTE/WLAN configuration
- router/antenna requirements
- monitoring system compatibility
''',
'''
------------------------------------------------------------
8. Abschnitt: DC-seitige Installationen
------------------------------------------------------------
Include:
- cable routing
- DC protection requirements
- grounding and equipotential bonding
- installation distance requirements
''',
'''
------------------------------------------------------------
9. Abschnitt: AC-seitige Installationen
------------------------------------------------------------
Include:
- routing inside/outside building
- house connection, Zählerschrank
- AC protections
- wall penetrations + fire sealing
- Wandler- oder Direktmessung (TAB-konform)
- NSHV connection requirements
''',
'''
------------------------------------------------------------
10. Abschnitt: Messkonzept
------------------------------------------------------------
Include:
- Einspeiseart (Volleinspeisung / Überschuss)
- required meters
- measurement direction
- VNB requirements
''',
'''
------------------------------------------------------------
11. Abschnitt: Brand- und Blitzschutz
------------------------------------------------------------
Include:
- compliance with building fire regulations
- cable routing outside building if possible
- fire walls and sealing (Brandschutzschott)
- integration into lightning protection concept
'''
]
