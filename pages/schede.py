import flet as ft
import threading
from services.local_db import get_local_workouts as get_schede

# --- Cache Globale ---
_cache_schede = None

def schede_view(page: ft.Page):
    user_email = page.session.store.get("user_email") or "atleta.gymlog@test.com"
    cards_column = ft.Column(spacing=10)
    
    loading_widget = ft.Row([
        ft.ProgressRing(color=ft.Colors.CYAN_400),
    ], alignment=ft.MainAxisAlignment.CENTER, visible=True)

    def andare_a_crea(e):
        page.session.store.remove("scheda_edit")
        page.go("/crea_scheda")

    def vai_a_modifica(scheda_data):
        page.session.store.set("scheda_edit", scheda_data)
        page.go("/crea_scheda")

    def esegui_cancellazione(scheda_id):
        global _cache_schede
        print(f"🗑️ Richiesta rimozione locale della scheda {scheda_id}")
        # Reset cache per forzare il ricaricamento dopo la modifica
        _cache_schede = None
        refresh_data()

    actions_row = ft.Row([
        ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.ADD, size=35, color="white"),
                ft.Text("Nuova Scheda", size=16, weight="bold", color="white")
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="#0ea5e9", 
            border_radius=15,
            padding=20,
            expand=True, 
            on_click=andare_a_crea,
            ink=True 
        ),
        ft.Container(width=10), 
        ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.LIST_ALT, size=35, color="#0ea5e9"),
                ft.Text("Gestisci Esercizi", size=16, weight="bold", color="#0ea5e9")
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="#1e293b", 
            border_radius=15,
            padding=20,
            expand=True,
            on_click=lambda e: page.go("/esercizi"), 
            ink=True
        )
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    def render_schede(unique_schede):
        cards_column.controls.clear()
        if not unique_schede:
            cards_column.controls.append(
                ft.Text("Nessuna scheda trovata. Creane una nuova!", color="grey", italic=True)
            )
        else:
            for s in unique_schede.values():
                titolo = s.get("nome_scheda", "Senza Titolo")
                split = s.get("split_type", "General")
                num_ex = len(s.get("esercizi", []))
                
                card = ft.Container(
                    content=ft.ListTile(
                        title=ft.Text(titolo, color="white", weight="bold"),
                        subtitle=ft.Text(f"Focus: {split} | {num_ex} Esercizi", color="#94a3b8"),
                        on_click=lambda e, data=s: [page.session.store.set("scheda_selezionata", data), page.go("/dettaglio")],
                        trailing=ft.PopupMenuButton(
                            items=[
                                ft.PopupMenuItem("Modifica", icon=ft.Icons.EDIT, on_click=lambda e, data=s: vai_a_modifica(data)),
                                ft.PopupMenuItem("Elimina", icon=ft.Icons.DELETE, on_click=lambda e, sid=s.get("id"): esegui_cancellazione(sid)),
                            ]
                        )
                    ),
                    bgcolor="#1e293b",
                    border_radius=12,
                    padding=5
                )
                cards_column.controls.append(card)
        loading_widget.visible = False
        page.update()

    def refresh_data():
        global _cache_schede
        loading_widget.visible = True
        page.update()

        # Uso cache se disponibile
        if _cache_schede is not None:
            render_schede(_cache_schede)
            return
        
        try:
            schede_list = get_schede(user_email)
            
            # --- LOGICA FILTRO ANTI-DUPLICATI E ANTI-ALLENAMENTI ---
            unique_schede = {}
            if schede_list:
                for s in schede_list:
                    if s.get("type") == "scheda" or ("split_type" in s and "durata" not in s):
                        s_id = s.get("id")
                        if s_id:
                            unique_schede[s_id] = s
            
            _cache_schede = unique_schede
            render_schede(unique_schede)
            
        except Exception as ex:
            print(f"Errore caricamento schede: {ex}")
            loading_widget.visible = False
            page.update()

    def nav_change(e):
        index = e.control.selected_index
        if index == 0: pass
        elif index == 1: page.go("/")
        elif index == 2: page.go("/workout")

    threading.Thread(target=refresh_data, daemon=True).start()

    return ft.View(
        route="/schede",
        bgcolor="#0f172a", 
        padding=ft.Padding.only(top=60, left=20, right=20, bottom=20), 
        controls=[
            ft.Column([
                ft.Container(
                    content=ft.Text("Le tue Schede", size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    margin=ft.Margin.only(bottom=20) 
                ),
                actions_row, 
                ft.Divider(color="transparent", height=20),
            ], spacing=0),
            
            ft.Container(
                content=ft.Column(
                    controls=[
                        loading_widget,
                        cards_column, 
                        ft.Container(height=50)
                    ],
                    scroll=ft.ScrollMode.AUTO,
                ),
                expand=True 
            )
        ],
        navigation_bar=ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.FOLDER_COPY, label="Schede"),
                ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
                ft.NavigationBarDestination(icon=ft.Icons.SPORTS_GYMNASTICS, label="Allenamento"),
            ],
            bgcolor="#1e293b",
            indicator_color=ft.Colors.BLUE_600, 
            selected_index=0,
            on_change=nav_change
        )
    )