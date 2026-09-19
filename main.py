import io
import os
import base64
import threading
import requests
from PIL import Image, ImageOps, ImageDraw
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image as KImage
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.utils import platform

APP_NAME = "Image Studio Local"
MODEL = "Qwen/Qwen-Image-Edit"
DEFAULT_PROMPT = (
    "Picture 1 is the adult model and identity reference. "
    "Picture 2 is the clothing reference. Replace only the clothing on the model "
    "with the clothing shown in Picture 2. Preserve the person's face, identity, "
    "body proportions, skin, hair, pose and camera perspective. Reproduce the "
    "reference clothing as faithfully as possible: exact color, fabric appearance, "
    "lace, seams, straps, shape, cut and details. Keep the result photorealistic, "
    "natural and suitable for an adult fashion/e-commerce catalog. "
    "Do not add nudity. "
)

class ImageStudio(App):
    def build(self):
        Window.clearcolor = (0.035, 0.035, 0.045, 1)
        self.main_path = ""
        self.ref_path = ""
        self.result_path = ""
        self.token = ""
        self.format_ratio = "9:16"

        root = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        title = Label(text="[b]IMAGE STUDIO[/b]", markup=True, font_size=dp(24),
                      size_hint_y=None, height=dp(42))
        root.add_widget(title)

        scroll = ScrollView(do_scroll_x=False)
        content = BoxLayout(orientation="vertical", spacing=dp(12), size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        self.status = Label(text="Pronto", size_hint_y=None, height=dp(30))
        content.add_widget(self.status)

        self.main_btn = Button(text="📷  FOTO DA MODELO", size_hint_y=None, height=dp(54))
        self.main_btn.bind(on_release=lambda *_: self.pick_file("main"))
        content.add_widget(self.main_btn)

        self.ref_btn = Button(text="👗  ROUPA DE REFERÊNCIA", size_hint_y=None, height=dp(54))
        self.ref_btn.bind(on_release=lambda *_: self.pick_file("ref"))
        content.add_widget(self.ref_btn)

        self.prompt = TextInput(text=DEFAULT_PROMPT, multiline=True, size_hint_y=None,
                                height=dp(150), padding=[dp(12), dp(12)])
        content.add_widget(Label(text="Prompt", size_hint_y=None, height=dp(25)))
        content.add_widget(self.prompt)

        content.add_widget(Label(text="Formato", size_hint_y=None, height=dp(25)))
        formats = GridLayout(cols=3, size_hint_y=None, height=dp(52), spacing=dp(7))
        for ratio in ("9:16", "1:1", "16:9"):
            b = Button(text=ratio)
            b.bind(on_release=lambda btn, r=ratio: self.set_ratio(r))
            formats.add_widget(b)
        content.add_widget(formats)

        self.generate_btn = Button(text="✨  GERAR IMAGEM", size_hint_y=None, height=dp(62))
        self.generate_btn.bind(on_release=self.generate)
        content.add_widget(self.generate_btn)

        self.result = KImage(allow_stretch=True, keep_ratio=True, size_hint_y=None, height=dp(420))
        content.add_widget(self.result)

        self.save_btn = Button(text="💾  SALVAR RESULTADO", size_hint_y=None, height=dp(54))
        self.save_btn.bind(on_release=self.save_result)
        content.add_widget(self.save_btn)

        scroll.add_widget(content)
        root.add_widget(scroll)
        return root

    def set_ratio(self, ratio):
        self.format_ratio = ratio
        self.status.text = f"Formato: {ratio}"

    def pick_file(self, kind):
        chooser = FileChooserListView(path="/storage/emulated/0",
                                      filters=["*.png", "*.jpg", "*.jpeg", "*.webp"],
                                      multiselect=False)
        box = BoxLayout(orientation="vertical")
        box.add_widget(chooser)
        buttons = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        cancel = Button(text="Cancelar")
        choose = Button(text="Usar imagem")
        buttons.add_widget(cancel); buttons.add_widget(choose)
        box.add_widget(buttons)
        popup = Popup(title="Escolha uma imagem", content=box, size_hint=(.96, .90))
        cancel.bind(on_release=popup.dismiss)

        def selected(*_):
            if chooser.selection:
                path = chooser.selection[0]
                if kind == "main":
                    self.main_path = path
                    self.main_btn.text = "✓  " + os.path.basename(path)[:28]
                else:
                    self.ref_path = path
                    self.ref_btn.text = "✓  " + os.path.basename(path)[:28]
                popup.dismiss()
        choose.bind(on_release=selected)
        popup.open()

    def set_status(self, text):
        Clock.schedule_once(lambda dt: setattr(self.status, "text", text))

    def make_contact_sheet(self, a, b):
        # One-image provider endpoint is used for maximum compatibility.
        # The two references are placed side-by-side and described explicitly.
        a = ImageOps.exif_transpose(a).convert("RGB")
        b = ImageOps.exif_transpose(b).convert("RGB")
        target_h = 768
        a = ImageOps.contain(a, (768, target_h))
        b = ImageOps.contain(b, (768, target_h))
        sheet = Image.new("RGB", (1536, target_h), "white")
        sheet.paste(a, ((768-a.width)//2, (target_h-a.height)//2))
        sheet.paste(b, (768+(768-b.width)//2, (target_h-b.height)//2))
        draw = ImageDraw.Draw(sheet)
        draw.rectangle((0, 0, 1535, 44), fill="black")
        draw.text((20, 12), "PICTURE 1 = MODEL / PICTURE 2 = CLOTHING REFERENCE", fill="white")
        return sheet

    def generate(self, *_):
        if not self.main_path or not self.ref_path:
            self.status.text = "Selecione a foto da modelo e a referência da roupa."
            return
        if not self.token.strip():
            self.ask_token()
            return

        self.generate_btn.disabled = True
        self.status.text = "Gerando… aguarde."
        threading.Thread(target=self._generate_thread, daemon=True).start()

    def ask_token(self):
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        box.add_widget(Label(text="Cole seu token HF_TOKEN do Hugging Face.\nEle fica salvo somente neste aparelho."))
        inp = TextInput(password=True, multiline=False)
        box.add_widget(inp)
        row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        cancel = Button(text="Cancelar")
        ok = Button(text="Salvar")
        row.add_widget(cancel); row.add_widget(ok); box.add_widget(row)
        pop = Popup(title="Token Hugging Face", content=box, size_hint=(.94, .55))
        cancel.bind(on_release=pop.dismiss)
        def save(*_):
            self.token = inp.text.strip()
            pop.dismiss()
            if self.token:
                self.generate()
        ok.bind(on_release=save)
        pop.open()

    def _generate_thread(self):
        try:
            a = Image.open(self.main_path)
            b = Image.open(self.ref_path)
            sheet = self.make_contact_sheet(a, b)
            buf = io.BytesIO()
            sheet.save(buf, format="PNG")
            data = buf.getvalue()

            prompt = (
                self.prompt.text.strip()
                + f" Final composition must use the requested {self.format_ratio} portrait/landscape ratio."
            )

            # Hugging Face's documented image_to_image route.
            url = "https://router.huggingface.co/hf-inference/models/" + MODEL
            headers = {"Authorization": f"Bearer {self.token}",
                       "Content-Type": "application/json"}
            payload = {
                "inputs": base64.b64encode(data).decode("ascii"),
                "parameters": {"prompt": prompt}
            }

            # Some router deployments accept raw bytes rather than JSON. Try the
            # documented SDK-compatible endpoint first, then raw body fallback.
            r = requests.post(url, headers=headers, json=payload, timeout=300)
            if r.status_code >= 400:
                r = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {self.token}",
                             "Content-Type": "application/octet-stream"},
                    data=data,
                    params={"prompt": prompt},
                    timeout=300
                )
            r.raise_for_status()

            out = Image.open(io.BytesIO(r.content)).convert("RGB")
            out_dir = os.path.join(self.user_data_dir, "gallery")
            os.makedirs(out_dir, exist_ok=True)
            self.result_path = os.path.join(out_dir, "result.png")
            out.save(self.result_path, "PNG")
            Clock.schedule_once(lambda dt: self._show_result(self.result_path))
        except Exception as e:
            Clock.schedule_once(lambda dt: self._error(str(e)))

    def _show_result(self, path):
        self.result.source = path
        self.result.reload()
        self.status.text = "Imagem gerada."
        self.generate_btn.disabled = False

    def _error(self, msg):
        self.status.text = "Erro: " + msg[:180]
        self.generate_btn.disabled = False

    def save_result(self, *_):
        if not self.result_path or not os.path.exists(self.result_path):
            self.status.text = "Gere uma imagem primeiro."
            return
        try:
            if platform == "android":
                from jnius import autoclass
                Environment = autoclass("android.os.Environment")
                MediaStore = autoclass("android.provider.MediaStore")
                ContentValues = autoclass("android.content.ContentValues")
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                resolver = PythonActivity.mActivity.getContentResolver()
                values = ContentValues()
                values.put(MediaStore.Images.Media.DISPLAY_NAME, "ImageStudioLocal.png")
                values.put(MediaStore.Images.Media.MIME_TYPE, "image/png")
                values.put(MediaStore.Images.Media.RELATIVE_PATH, "Pictures/ImageStudioLocal")
                uri = resolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values)
                if uri:
                    out = resolver.openOutputStream(uri)
                    with open(self.result_path, "rb") as f:
                        out.write(f.read())
                    out.close()
                    self.status.text = "Salvo em Fotos/Pictures/ImageStudioLocal."
                    return
            self.status.text = "Resultado salvo dentro do armazenamento do app."
        except Exception as e:
            self.status.text = "Salvo no app; erro ao exportar: " + str(e)[:100]

if __name__ == "__main__":
    ImageStudio().run()
