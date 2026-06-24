import flet as ft
import threading
import json
import os
import uuid

def gestione_esercizi_view(page: ft.Page):
    # Usiamo user_address invece di user_email per coerenza DApp
    user_address = page.session.store.get("user_address")
    
    exercises_column = ft.Column(spacing=10)
    loading = ft.ProgressRing(color=ft.Colors.CYAN_400, visible=True)

    DB_FILE = "local_data/custom_esercizi.json"

    def get_saved_esercizi():
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r") as f:
                    return json.load(f)
            except: return []
        return []

    def load_data():
        exercises_column.controls.clear()
        loading.visible = True
        page.update()
        
        # Uniamo gli esercizi di base a quelli salvati dall'utente
        base_items = ["Panca Piana", "Squat", "Stacco da terra", "Trazioni", "Lento Avanti", "Bicipiti Bilanciere"]
        custom_items = get_saved_esercizi()
        
        items = base_items + custom_items
        loading.visible = False
        
        if not items:
            exercises_column.controls.append(ft.Text("Nessun esercizio trovato.", color="grey"))
        else:
            for item in items:
                if isinstance(item, str):
                    ex_name = item
                    ex_id = None 
                    owner = "system" 
                    is_mine = False 
                else:
                    ex_name = item.get("exercise_name", "???")
                    ex_id = item.get("id")
                    owner = item.get("user_address")
                    is_mine = (owner == user_address) and (ex_id is not None)
                
                card = ft.Container(
                    content=ft.Row([
                        ft.Row([
                            ft.Icon(ft.Icons.FITNESS_CENTER, color="grey", size=16),
                            ft.Text(ex_name, color="white", size=16, weight="bold"),
                        ]),
                        
                        ft.IconButton(
                            ft.Icons.DELETE_OUTLINE, 
                            icon_color="red", 
                            visible=is_mine,
                            tooltip="Elimina esercizio personale",
                            on_click=lambda e, x=ex_id: delete_click(x)
                        ) if is_mine else ft.Icon(ft.Icons.LOCK, color="#334155", size=16, tooltip="Sistema")
                        
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor="#1e293b", padding=15, border_radius=10, 
                    border=ft.border.all(1, "#334155")
                )
                exercises_column.controls.append(card)
        page.update()

    def show_snack(msg, color):
        snack = ft.SnackBar(ft.Text(msg, color="white", weight="bold"), bgcolor=color)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def delete_click(ex_id):
        if not ex_id: return
        saved = get_saved_esercizi()
        saved = [ex for ex in saved if ex.get("id") != ex_id]
        with open(DB_FILE, "w") as f:
            json.dump(saved, f)
        
        show_snack("Esercizio eliminato!", "orange")
        load_data() 

    txt_new_name = ft.TextField(label="Nome Esercizio", bgcolor="#1e293b", border_color="#334155", color="white")

    def close_add_dialog(e=None):
        dlg_add.open = False
        page.update()

    def confirm_add(e):
        if not txt_new_name.value: return
        
        new_ex = {
            "id": str(uuid.uuid4()),
            "exercise_name": txt_new_name.value,
            "user_address": user_address
        }
        
        os.makedirs("local_data", exist_ok=True)
        saved = get_saved_esercizi()
        saved.append(new_ex)
        
        with open(DB_FILE, "w") as f:
            json.dump(saved, f)
            
        txt_new_name.value = ""
        dlg_add.open = False
        show_snack("Esercizio salvato!", "green")
        load_data()

    dlg_add = ft.AlertDialog(
        title=ft.Text("Nuovo Esercizio"),
        content=txt_new_name,
        actions=[
            ft.TextButton("Annulla", on_click=close_add_dialog),
            ft.ElevatedButton("Salva", on_click=confirm_add, bgcolor=ft.Colors.CYAN_600, color="white")
        ]
    )

    def open_add_dialog(e):
        if dlg_add not in page.overlay:
            page.overlay.append(dlg_add)
        dlg_add.open = True
        page.update()

    view = ft.View(
        route="/esercizi",
        bgcolor="#0f172a",
        padding=ft.Padding(top=60, left=20, right=20, bottom=20),
        controls=[
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK_IOS, icon_color="white", on_click=lambda e: page.go("/schede")),
                ft.Text("Gestione Esercizi", size=24, weight="bold", color="white")
            ]),
            ft.Divider(color="transparent", height=20),
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.ADD_CIRCLE, color="white"),
                    ft.Text("Crea Nuovo Esercizio", color="white", weight="bold")
                ], alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=ft.Colors.CYAN_700, padding=15, border_radius=10,
                on_click=open_add_dialog,
                ink=True
            ),
            ft.Divider(color="transparent", height=20),
            loading,
            ft.Container(content=exercises_column, expand=True)
        ],
        scroll=ft.ScrollMode.AUTO
    )
    
    threading.Thread(target=load_data, daemon=True).start()
    return view