import flet as ft
import threading
from services.local_db import get_local_workouts as get_workout_logs

def workout_view(page: ft.Page):
    user_email = page.session.store.get("user_email")
    
    history_column = ft.ListView(
        spacing=10, 
        expand=True, 
        padding=ft.Padding(left=0, top=0, right=10, bottom=100)
    )
    
    loading_history = ft.ProgressRing(color=ft.Colors.CYAN_400)
    
    def open_detail_page(e, log_data):
        page.session.store.set("allenamento_selezionato", log_data)
        page.go("/dettaglio_allenamento")

    import flet as ft
import threading
from services.local_db import get_local_workouts as get_workout_logs

# --- Cache Globale ---
_cache_storico = None

def workout_view(page: ft.Page):
    user_email = page.session.store.get("user_email")
    
    history_column = ft.ListView(spacing=10, expand=True, padding=ft.Padding.only(left=0, top=0, right=10, bottom=100))
    loading_history = ft.ProgressRing(color=ft.Colors.CYAN_400)
    
    def render_logs(logs):
        history_column.controls.clear()
        if not logs:
            history_column.controls.append(ft.Container(content=ft.Text("Nessun allenamento.", color="grey"), padding=20))
        else:
            for log in logs:
                # ... (qui va il tuo codice esistente per creare le card) ...
                pass
        loading_history.visible = False
        page.update()

    def load_history():
        global _cache_storico
        # Se la cache esiste, usa quella
        if _cache_storico is not None:
            render_logs(_cache_storico)
            return

        # Altrimenti carica dal disco e salva in cache
        logs = get_workout_logs(user_email)
        _cache_storico = logs if logs else []
        render_logs(_cache_storico)

    # Avvio caricamento in background
    threading.Thread(target=load_history, daemon=True).start()
    

    def start_workout(scheda):
        page.session.store.set("workout_active_scheda", scheda)
        bs_schede.open = False 
        page.update()
        page.go("/live_workout")

    bs_schede_content = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=10)
    
    bs_schede = ft.BottomSheet(
        ft.Container(
            content=bs_schede_content,
            padding=20,
            bgcolor="#1e293b",
            border_radius=ft.BorderRadius(top_left=20, top_right=20, bottom_left=0, bottom_right=0),
            height=500 
        )
    )

    def open_start_dialog(e):
        from services.local_db import get_local_workouts as get_schede
        schede = get_schede(user_email)
        bs_schede_content.controls.clear()
        
        bs_schede_content.controls.append(
            ft.Container(
                content=ft.Text("Scegli la scheda", size=20, weight="bold", color="white"),
                padding=ft.Padding(bottom=10)
            )
        )
        
        # Filtriamo le schede reali valide da mostrare nella tendina di inizio allenamento
        valid_schede = [s for s in schede if s.get("type") == "scheda" or ("split_type" in s and "durata" not in s)] if schede else []
        
        # Elimina i duplicati per ID anche dalla tendina di selezione iniziale
        unique_start_schede = {}
        for s in valid_schede:
            if s.get("id"): unique_start_schede[s["id"]] = s

        if not unique_start_schede:
            bs_schede_content.controls.append(ft.Text("Nessuna scheda trovata. Creane una prima!", color="red"))
        else:
            for s in unique_start_schede.values():
                tile = ft.ListTile(
                    leading=ft.Icon(ft.Icons.FITNESS_CENTER, color=ft.Colors.CYAN_400),
                    title=ft.Text(s.get("nome_scheda"), color="white", weight="bold"),
                    subtitle=ft.Text(f"{len(s.get('esercizi', []))} Esercizi", color="grey"),
                    on_click=lambda e, x=s: start_workout(x),
                    bgcolor="#0f172a",
                )
                bs_schede_content.controls.append(tile)
        
        if bs_schede not in page.overlay:
            page.overlay.append(bs_schede)
        bs_schede.open = True
        page.update()

    def nav_change(e):
        index = e.control.selected_index
        if index == 0: page.go("/schede")
        elif index == 1: page.go("/")
        elif index == 2: pass 

    return ft.View(
        route="/workout",
        bgcolor="#0f172a",
        padding=ft.Padding(top=60, left=0, right=0, bottom=0), 
        controls=[
            ft.Container(
                padding=20,
                expand=True,
                content=ft.Column([
                    ft.Text("Storico Allenamenti", size=28, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Divider(color="transparent", height=10),
                    
                    ft.Row([loading_history], alignment=ft.MainAxisAlignment.CENTER),
                    
                    history_column
                ], expand=True) 
            )
        ],
        floating_action_button=ft.FloatingActionButton(
            bgcolor=ft.Colors.CYAN_600,
            content=ft.Row([ft.Icon(ft.Icons.PLAY_ARROW), ft.Text("INIZIA", weight="bold")], alignment=ft.MainAxisAlignment.CENTER),
            width=120,
            on_click=open_start_dialog
        ),
        floating_action_button_location=ft.FloatingActionButtonLocation.CENTER_FLOAT,
        navigation_bar=ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.FOLDER_COPY, label="Schede"),
                ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
                ft.NavigationBarDestination(icon=ft.Icons.SPORTS_GYMNASTICS, label="Allenamento"),
            ],
            bgcolor="#1e293b",
            indicator_color=ft.Colors.BLUE_600,
            selected_index=2,
            on_change=nav_change
        )
    )