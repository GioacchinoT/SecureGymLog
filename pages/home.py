import flet as ft
import threading
from services.local_db import get_local_workouts

def home_view(page: ft.Page):
    # Con il login Web3 l'identità è il wallet address
    user_address = page.session.store.get("user_address")
    user_name    = page.session.store.get("user_name") or "Atleta"

    cached_weight = page.session.store.get("user_weight")
    cached_height = page.session.store.get("user_height")
    cached_age    = page.session.store.get("user_age")

    user_weight = cached_weight or "inserisci dati"
    user_height = cached_height or "inserisci dati"
    user_age    = cached_age    or "inserisci dati"

    if cached_weight and cached_height and cached_age:
        print("--> Dati utente caricati dalla cache locale.")

    # --- METRICHE BMI / BMR ---
    lbl_bmi_val  = ft.Text("--", size=30, weight="bold", color="white")
    lbl_bmi_desc = ft.Text("...", size=14, color="grey")
    lbl_bmr_val  = ft.Text("--", size=30, weight="bold", color="white")

    def calculate_metrics():
        try:
            w = float(user_weight)
            h = float(user_height)
            a = float(user_age)
            bmi = w / ((h / 100) ** 2)
            lbl_bmi_val.value = f"{bmi:.1f}"
            if   bmi < 18.5: lbl_bmi_desc.value, lbl_bmi_desc.color = "Sottopeso", "orange"
            elif bmi < 25:   lbl_bmi_desc.value, lbl_bmi_desc.color = "Normopeso",  "green"
            elif bmi < 30:   lbl_bmi_desc.value, lbl_bmi_desc.color = "Sovrappeso", "orange"
            else:             lbl_bmi_desc.value, lbl_bmi_desc.color = "Obeso",      "red"
            bmr = (10 * w) + (6.25 * h) - (5 * a) + 5
            lbl_bmr_val.value = f"{int(bmr)}"
        except Exception:
            lbl_bmi_val.value = "--"
            lbl_bmr_val.value = "--"
        page.update()

    # --- DIALOG MODIFICA DATI ---
    txt_edit_weight = ft.TextField(label="Peso (kg)",    value=user_weight, bgcolor="#1e293b", color="white", border_color="#334155")
    txt_edit_height = ft.TextField(label="Altezza (cm)", value=user_height, bgcolor="#1e293b", color="white", border_color="#334155")
    txt_edit_age    = ft.TextField(label="Età",          value=user_age,    bgcolor="#1e293b", color="white", border_color="#334155")

    def save_stats(e):
        nonlocal user_weight, user_height, user_age
        user_weight = txt_edit_weight.value
        user_height = txt_edit_height.value
        user_age    = txt_edit_age.value
        lbl_weight.value = f"{user_weight} kg"
        lbl_height.value = f"{user_height} cm"
        lbl_age.value    = f"{user_age} anni"
        page.session.store.set("user_weight", user_weight)
        page.session.store.set("user_height", user_height)
        page.session.store.set("user_age",    user_age)
        calculate_metrics()
        page.close(dialog_edit)
        page.update()

    dialog_edit = ft.AlertDialog(
        modal=True,
        title=ft.Text("Aggiorna i tuoi dati"),
        bgcolor="#0f172a",
        content=ft.Column([txt_edit_weight, txt_edit_height, txt_edit_age], height=200, tight=True),
        actions=[
            ft.TextButton("Annulla", on_click=lambda e: page.close(dialog_edit)),
            ft.ElevatedButton("Salva", on_click=save_stats, bgcolor=ft.Colors.BLUE_600, color="white")
        ]
    )

    # --- STATISTICHE ALLENAMENTI ---
    cached_num_schede = page.session.store.get("stats_num_schede") or "..."
    cached_num_ex     = page.session.store.get("stats_num_ex")     or "..."

    lbl_count_schede   = ft.Text(str(cached_num_schede), size=24, weight="bold", color=ft.Colors.CYAN_400)
    lbl_count_esercizi = ft.Text(str(cached_num_ex),     size=24, weight="bold", color=ft.Colors.PURPLE_400)

    def load_gym_stats():
        if not user_address:
            return
        try:
            tutti = get_local_workouts(user_address)
            schede = [s for s in tutti if s.get("type") == "scheda"
                      or ("split_type" in s and "durata" not in s)]
            num_schede = len(schede)
            num_ex     = sum(len(s.get('esercizi', [])) for s in schede)
            lbl_count_schede.value   = str(num_schede)
            lbl_count_esercizi.value = str(num_ex)
            page.session.store.set("stats_num_schede", num_schede)
            page.session.store.set("stats_num_ex",     num_ex)
            page.update()
        except Exception as e:
            print(f"Errore stats: {e}")

    threading.Thread(target=load_gym_stats, daemon=True).start()

    # --- UI ---
    def stat_mini_card(icon, label, value_ref, color):
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, color=color, size=24),
                ft.Text(label, size=12, color="grey"),
                value_ref
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="#1e293b", padding=15, border_radius=15, expand=True,
            border=ft.Border.all(1, "#334155")
        )

    def big_metric_card(title, value_ctrl, subtitle_ctrl, icon, color):
        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(icon, color=color), ft.Text(title, weight="bold", color=color)]),
                ft.Container(height=5),
                value_ctrl,
                subtitle_ctrl
            ]),
            bgcolor="#1e293b", padding=20, border_radius=15, expand=True
        )

    lbl_weight = ft.Text(f"{user_weight} kg", weight="bold", color="white")
    lbl_height = ft.Text(f"{user_height} cm", weight="bold", color="white")
    lbl_age    = ft.Text(f"{user_age} anni",  weight="bold", color="white")

    # Mostra l'indirizzo wallet abbreviato come "nome utente"
    wallet_display = f"{user_address[:6]}...{user_address[-4:]}" if user_address else "N/A"

    header = ft.Row([
        ft.Column([
            ft.Text(f"Ciao, {user_name}", size=28, weight=ft.FontWeight.BOLD, color="white", no_wrap=False),
            ft.Text(wallet_display, size=12, color="#64748b", font_family="monospace"),
        ], expand=True),
        ft.IconButton(ft.Icons.LOGOUT, icon_color="red", tooltip="Esci",
                      on_click=lambda e: [page.session.store.clear(), page.go("/welcome")])
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    physical_stats_row = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("I tuoi dati", weight="bold", color="white", size=16),
                ft.IconButton(ft.Icons.EDIT, icon_color=ft.Colors.BLUE_400, icon_size=20,
                              on_click=lambda e: page.open(dialog_edit))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row([
                stat_mini_card(ft.Icons.MONITOR_WEIGHT, "PESO",    lbl_weight, ft.Colors.BLUE_400),
                ft.Container(width=10),
                stat_mini_card(ft.Icons.HEIGHT,         "ALTEZZA", lbl_height, ft.Colors.BLUE_400),
                ft.Container(width=10),
                stat_mini_card(ft.Icons.CAKE,           "ETÀ",     lbl_age,    ft.Colors.BLUE_400),
            ])
        ]),
        bgcolor="#0f172a",
        margin=ft.Margin.only(bottom=20)
    )

    metrics_row = ft.Row([
        big_metric_card("BMI", lbl_bmi_val, lbl_bmi_desc,
                        ft.Icons.HEALTH_AND_SAFETY, ft.Colors.GREEN_400),
        ft.Container(width=10),
        big_metric_card("BMR (Kcal)", lbl_bmr_val,
                        ft.Text("Kcal/giorno", color="grey", size=12),
                        ft.Icons.LOCAL_FIRE_DEPARTMENT, ft.Colors.ORANGE_400)
    ])

    gym_stats_card = ft.Container(
        content=ft.Column([
            ft.Text("Overview Allenamenti", size=16, weight="bold", color="white"),
            ft.Divider(color="transparent", height=10),
            ft.Row([
                ft.Column([lbl_count_schede,   ft.Text("Schede Create",    color="grey", size=12)],
                          expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(width=1, height=40, bgcolor="#334155"),
                ft.Column([lbl_count_esercizi, ft.Text("Esercizi Aggiunti", color="grey", size=12)],
                          expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ])
        ]),
        bgcolor="#1e293b", padding=20, border_radius=15,
        border=ft.Border.all(1, ft.Colors.CYAN_900),
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.CYAN_900, offset=ft.Offset(0, 0))
    )

    def nav_change(e):
        index = e.control.selected_index
        if   index == 0: page.go("/schede")
        elif index == 1: pass
        elif index == 2: page.go("/workout")

    calculate_metrics()

    return ft.View(
        route="/",
        bgcolor="#0f172a",
        padding=ft.Padding.only(top=60, left=20, right=20, bottom=20),
        scroll=ft.ScrollMode.AUTO,
        controls=[
            header,
            ft.Divider(color="transparent", height=20),
            physical_stats_row,
            metrics_row,
            ft.Divider(color="transparent", height=20),
            gym_stats_card
        ],
        navigation_bar=ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.FOLDER_COPY, label="Schede"),
                ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
                ft.NavigationBarDestination(icon=ft.Icons.SPORTS_GYMNASTICS, label="Allenamento"),
            ],
            bgcolor="#1e293b",
            indicator_color=ft.Colors.BLUE_600,
            selected_index=1,
            on_change=nav_change
        )
    )
