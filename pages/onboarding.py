import flet as ft
from web3 import Web3

def onboarding_view(page: ft.Page):
    error_txt = ft.Text("", color="red", size=14, weight="bold")

    # Inizializziamo la connessione Web3 verso il nostro nodo locale
    w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

    # Campo di input grafico per inserire la chiave privata Ethereum
    pk_input = ft.TextField(
        label="Chiave Privata Ethereum (Hex)",
        password=True,
        can_reveal_password=True,
        width=300,
        border_color=ft.Colors.BLUE_600,
        focused_border_color=ft.Colors.BLUE_ACCENT,
        color="white"
    )

    # --- LOGICA DI LOGIN DECENTRALIZZATA WEB3 ---
    def start_login_click(e):
        pk = pk_input.value.strip()

        # Pulizia dell'input: rimuoviamo l'eventuale prefisso '0x' inserito dall'utente
        if pk.startswith("0x"):
            pk = pk[2:]

        # AGGIUNGI QUESTA RIGA PER DEBUGGARE
        print(f"DEBUG: Lunghezza PK inserita: {len(pk)}")

        # Validazione formale della lunghezza di una chiave privata esadecimale (256 bit = 64 caratteri)
        if not pk or len(pk) != 64:
            error_txt.value = "Errore: Inserisci una chiave privata esadecimale valida (64 caratteri)."
            page.update()
            return

        btn_login.disabled = True
        loading_ring_main.visible = True
        page.update()
        
        try:
            # Sfruttiamo la crittografia asimmetrica: deriviamo matematicamente l'account dalla chiave privata
            account = w3.eth.account.from_key(pk)
            user_address = account.address
            
            # Verifichiamo se il client Web3 riesce a dialogare con la blockchain locale
            if not w3.is_connected():
                error_txt.value = "Errore: Impossibile connettersi al nodo Hardhat. Avvialo prima."
                btn_login.disabled = False
                loading_ring_main.visible = False
                page.update()
                return

            # Salvataggio sicuro dei parametri crittografici nella sessione isolata di Flet
            page.session.store.set("user_address", user_address)
            page.session.store.set("private_key", "0x" + pk)
            
            # Mantieni variabili legacy per retrocompatibilità temporanea con i vecchi widget dell'interfaccia
            page.session.store.set("user_email", f"{user_address[:8]}...@hardhat.local")
            page.session.store.set("user_name", f"Wallet {user_address[:6]}")
            page.session.store.set("oid", f"eth_{user_address}")
            
            print(f"🔒 Autenticazione Web3 completata. Indirizzo derivato: {user_address}")
            
            # Reindirizzamento alla dashboard principale (Home)
            page.go("/")
            
        except Exception as ex:
            error_txt.value = f"Chiave non valida o errore di rete: {str(ex)}"
            btn_login.disabled = False
            loading_ring_main.visible = False
            page.update()

    # Componenti visivi del bottone di login
    btn_text = ft.Text("Accedi con il tuo Wallet", color="white", weight="bold", size=16)
    loading_ring_main = ft.ProgressRing(width=20, height=20, stroke_width=2, color="white", visible=False)
    btn_icon = ft.Icon(ft.Icons.KEY_ROUNDED, color="white", size=20)

    btn_login = ft.Container(
        content=ft.Row([btn_icon, btn_text, loading_ring_main], alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=ft.Colors.BLUE_600,
        padding=12,
        border_radius=8,
        width=300,
        on_click=start_login_click,
        # MODIFICATO: ft.Animation ora richiede ft.AnimationCurve enum invece della stringa "easeOut"
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT)
    )

    return ft.View(
        route="/welcome",
        padding=ft.Padding(top=60, left=20, right=20, bottom=20), 
        bgcolor="#0f172a",
        controls=[
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.FITNESS_CENTER, size=80, color=ft.Colors.BLUE_600),
                    ft.Text("SecureGymLog", size=40, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Text("Architettura Decentralizzata & Privacy by Design", size=16, color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=30), # Sostituisce il VerticalDivider
                    pk_input,
                    ft.Container(height=15), # Sostituisce il VerticalDivider
                    btn_login,
                    ft.Container(height=15), # Sostituisce il VerticalDivider
                    error_txt
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                # MODIFICATO: ft.alignment.center → ft.Alignment.CENTER (breaking change da Flet 0.80+)
                alignment=ft.Alignment.CENTER,
                expand=True
            )
        ]
    )
