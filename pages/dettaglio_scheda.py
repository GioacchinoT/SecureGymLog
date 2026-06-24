import flet as ft

def dettaglio_view(page: ft.Page):
    scheda = page.session.store.get("scheda_selezionata")
    
    if not scheda:
        page.go("/schede")
        return ft.View("/dettaglio", controls=[])

    titolo = scheda.get("nome_scheda", "Senza Titolo")
    split = scheda.get("split_type", "Nessun split specificato")
    data_creazione = scheda.get("created_at", "Sconosciuta")
    lista_esercizi = scheda.get("esercizi", [])
    
    esercizi_controls = []
    
    if not lista_esercizi:
        esercizi_controls.append(ft.Text("Nessun esercizio in questa scheda.", color="grey", italic=True))
    else:
        for i, ex in enumerate(lista_esercizi):
            nome_ex = ex.get("exercise_name", ex.get("nome", "Esercizio"))
            serie = ex.get("serie", "?")
            reps = ex.get("ripetizioni", "?")
            note = ex.get("note_ai", "")
            
            row = ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text(str(i+1), color="black", weight="bold"),
                        bgcolor=ft.Colors.BLUE_400, width=30, height=30, border_radius=15,
                        # FIX: ft.alignment.center → ft.Alignment.CENTER
                        alignment=ft.Alignment.CENTER
                    ),
                    ft.Container(width=10),
                    ft.Column([
                        ft.Text(nome_ex, size=16, weight="bold", color="white"),
                        ft.Text(f"{serie} Serie  x  {reps} Reps", color="#94a3b8", size=14),
                        ft.Text(f"Note: {note}", size=12, color="#5b6494") if note else ft.Container()
                    ], expand=True),
                ]),
                padding=15,
                bgcolor="#1e293b",
                border_radius=12,
                # FIX: ft.border.all() → ft.Border.all()
                border=ft.Border.all(1, "#334155")
            )
            esercizi_controls.append(row)

    def go_edit(e):
        page.session.store.set("scheda_edit", scheda)
        page.go("/crea_scheda")

    return ft.View(
        route="/dettaglio",
        bgcolor="#0f172a",
        padding=ft.Padding(top=60, left=20, right=20, bottom=20),
        controls=[
            ft.Row([
                ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK_IOS, icon_color="white", on_click=lambda e: page.go("/schede")),
                    ft.Text("Dettagli Scheda", size=20, weight="bold", color="white"),
                ]),
                ft.IconButton(
                    ft.Icons.EDIT,
                    icon_color=ft.Colors.CYAN_400,
                    tooltip="Modifica Scheda",
                    on_click=go_edit
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Divider(color="transparent", height=10),
            
            ft.Container(
                content=ft.Column([
                    ft.Text(titolo, size=24, weight="bold", color=ft.Colors.CYAN_400),
                    ft.Row([
                        ft.Icon(ft.Icons.CALENDAR_MONTH, size=16, color="grey"),
                        ft.Text(f"Creata il: {data_creazione}", color="grey", size=12),
                    ]),
                    ft.Row([
                        ft.Icon(ft.Icons.STYLE, size=16, color="grey"),
                        ft.Text(f"Tipo: {split}", color="grey", size=12),
                    ]),
                ]),
                padding=20,
                bgcolor="#1e293b",
                border_radius=15,
                # FIX: ft.border.only() → ft.Border(left=...) 
                border=ft.Border(left=ft.BorderSide(5, ft.Colors.CYAN_400))
            ),
            
            ft.Divider(color="transparent", height=20),
            ft.Text(f"ESERCIZI ({len(lista_esercizi)})", size=14, weight="bold", color="#94a3b8"),
            ft.Container(height=10),
            
            ft.Column(
                controls=esercizi_controls,
                scroll=ft.ScrollMode.AUTO,
                expand=True
            )
        ]
    )