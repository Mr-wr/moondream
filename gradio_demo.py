import torch
import re
import gradio as gr
from moondream import Moondream, detect_device
from huggingface_hub import snapshot_download
from threading import Thread
from transformers import TextIteratorStreamer, CodeGenTokenizerFast as Tokenizer

device, dtype = detect_device()
if device != torch.device("cpu"):
    print("Using device:", device)
    print("If you run into issues, pass the `--cpu` flag to this script.")
    print()

model_id = "vikhyatk/moondream1"
moondream = Moondream.from_pretrained(model_id).to(device=device, dtype=dtype)
vision_encoder = moondream.vision_encoder
text_model = moondream.text_model

model_path = snapshot_download("vikhyatk/moondream1")
tokenizer = Tokenizer.from_pretrained(f"{model_path}/tokenizer")
text_model.tokenizer = tokenizer


def moondream(img, prompt):
    image_embeds = vision_encoder(img)
    streamer = TextIteratorStreamer(text_model.tokenizer, skip_special_tokens=True)
    thread = Thread(
        target=text_model.answer_question,
        kwargs={"image_embeds": image_embeds, "question": prompt, "streamer": streamer},
    )
    thread.start()

    buffer = ""
    for new_text in streamer:
        clean_text = re.sub("<$|END$", "", new_text)
        buffer += clean_text
        yield buffer.strip("<END")


with gr.Blocks() as demo:
    gr.Markdown(
        """
        # 🌔 moondream
        ### A tiny vision language model. [GitHub](https://github.com/vikhyat/moondream)
        """
    )
    with gr.Row():
        prompt = gr.Textbox(label="Input Prompt", placeholder="Type here...", scale=4)
        submit = gr.Button("Submit")
    with gr.Row():
        img = gr.Image(type="pil", label="Upload an Image")
        output = gr.TextArea(label="Response", info="Please wait for a few seconds..")
    submit.click(moondream, [img, prompt], output)
    prompt.submit(moondream, [img, prompt], output)

demo.queue().launch(debug=True)