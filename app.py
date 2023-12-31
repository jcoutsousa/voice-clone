import streamlit as st

import genai
from voiceclone import *
from pdfreading import *
from elevenlabs import voices, set_api_key
from audiorecorder import audiorecorder
import re
import numpy as np
import os
import tempfile
import fitz
from openai import OpenAI
import pydub

# Load your API key from an environment variable or secret management service
#load_dotenv()  # take environment variables from .env

# Set the API key
os.environ["ELEVEN_API_KEY"] == st.secrets["ELEVEN_API_KEY"]
os.environ["OPENAI_API_KEY"] == st.secrets["OPENAI_API_KEY"]
client = OpenAI()


languages = ["English", "Portuguese-PT", "Chinese", "German", "French", "Spanish"]

def get_voices():
    all_voices = voices()
    voice_name = []
    for i in range(len(all_voices)):
        data_str = str(all_voices[i])

        # Use regular expression to extract the value associated with 'name'
        match = re.search(r"name='([^']+)'", data_str)
        if match:
            name = match.group(1)
            voice_name.append(name)

        else:
            print("Name not found in the string.")

    voice_name = np.array(voice_name)
    print(voice_name)
    return voice_name


if __name__ == "__main__":

    st.header("Voice Clone")

    action = st.radio(
        "What do you want to do?",
        ["Create a text with a available voice", "Create a custom voice"],
        captions=["Put the text you want", "Let's do it."])

    if action == 'Create a text with a available voice':

        voice_selection = st.selectbox("Select a voice", get_voices())
        text_selection = st.selectbox("Select the source", ["Writing text", 'Upload audio', 'Upload pdf'])

        if text_selection == 'Upload pdf':
            with st.form("Info", clear_on_submit=True):
                uploaded_file = st.file_uploader('Choose your .pdf file', type="pdf")
                if uploaded_file is not None:
                    temp_dir = tempfile.mkdtemp()
                    path = os.path.join(temp_dir, uploaded_file.name)
                    print(path)
                    with open(path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                        # To convert to a string based IO:
                        doc = fitz.open(f)
                        font_counts, styles = fonts(doc, granularity=False)
                        size_tag = font_tags(font_counts, styles)
                        text = headers_para(doc, size_tag)
                        # save to file
                        np.savetxt("Final.txt", text, fmt='%s')
                        new_text = []
                        #final_text = str(text)
                        for i in np.arange(len(text)):
                            if text[i] != "":
                                new_text.append(text[i])
                        final_text=''.join(new_text)
                        final_text_limit = final_text[:4999]
                        st.write(len(final_text_limit))
                submitted_file = st.form_submit_button("Submit")
                if submitted_file:
                    st.audio(voice_custom(final_text_limit, voice_name=voice_selection))
                    st.write(final_text_limit)
                    #st.audio(voice_custom('./Final.txt', voice_name=voice_selection))
        elif text_selection == 'Writing text':
            with st.form("Info", clear_on_submit=True):
                final_text = st.text_area('Type here the text you want.', max_chars=5000)
                translate_on = st.toggle('Translate')
                if translate_on is not None:
                    translation = st.selectbox("Select the language to translate audio", languages)
                    final_text_tran = genai.translate(translation, final_text)
                submitted_text = st.form_submit_button("Submit")
                if submitted_text and translate_on:
                    st.audio(voice_custom(final_text_tran, voice_name=voice_selection))
                    st.write(final_text_tran)
                elif submitted_text:
                    st.audio(voice_custom(final_text, voice_name=voice_selection))
                else:
                    st.write("Provide a text.")
        else:
            with st.form("Info", clear_on_submit=True):
                uploaded_file = st.file_uploader('Choose your audio file', type=["mp3","wav"])
                translate_on_audio = st.toggle('Translate')
                if translate_on_audio is not None:
                    translation_audio = st.selectbox("Select the language to translate audio", languages)
                if uploaded_file and translate_on_audio:
                    if uploaded_file.name.endswith('wav'):
                        audio = pydub.AudioSegment.from_wav(uploaded_file)
                        audio.export("audio_text.wav", format="wav")
                        audio_file = open("audio_text.wav", "rb")
                        transcript_original = genai.speech2text(audio_file)
                        transcript = genai.translate(translation_audio, transcript_original)
                    elif uploaded_file.name.endswith('mp3'):
                        audio = pydub.AudioSegment.from_mp3(uploaded_file)
                        audio.export("audio_text.mp3", format="mp3")
                        audio_file = open("audio_text.mp3", "rb")
                        transcript = genai.speech2text(audio_file)
                        transcript_original = genai.speech2text(audio_file)
                        transcript = genai.translate(translation_audio, transcript_original)
                elif uploaded_file:
                    audio = pydub.AudioSegment.from_wav(uploaded_file)
                    audio.export("audio_text.wav", format="wav")
                    audio_file = open("audio_text.wav", "rb")
                    transcript = genai.speech2text(audio_file)
                else:
                    st.write("Upload an audio file.")
                submitted_audio = st.form_submit_button("Submit")
                if submitted_audio:
                    st.audio(voice_custom(transcript, voice_name=voice_selection))
                    st.write(transcript)


    else:

        new_voice_name = st.text_area('Name')

        action_create = st.radio(
            "What do you want to do?",
            ["Record a voice", "Clone using a audio file"],
            captions=["Great!", "Amazinhg"])

        if action_create == "Record a voice":

            description = st.text_area("Ler este texto. Se quiser editar, coloque outro texto.",
            "It was the best of times, it was the worst of times, it was the age of "
            "wisdom, it was the age of foolishness, it was the epoch of belief, it "
            "was the epoch of incredulity, it was the season of Light, it was the "
            "season of Darkness, it was the spring of hope, it was the winter of "
            "despair, (...)")  # Optional

            if description:

                audio = audiorecorder("Click to record", "Click to stop recording")

                if len(audio) > 0:
                    # To play audio in frontend:
                    st.audio(audio.export().read())

                    # To save audio to a file, use pydub export method:
                    audio.export("audio.wav", format="wav")

                    # To get audio properties, use pydub AudioSegment properties:
                    st.write(
                        f"Frame rate: {audio.frame_rate}, Frame width: {audio.frame_width}, Duration: {audio.duration_seconds} seconds")

                    files = ['./audio.wav']

                    new_voice = voice_clone(new_voice_name, 'A custom voice', files)

                    if new_voice:
                        text_new = st.text_input('Type here the text you want.')

                        if text_new:
                            st.audio(voice_custom(text_new, voice_name=new_voice_name))

        else:
            with st.form("Info", clear_on_submit=True):
                uploaded_audio_voice = st.file_uploader('Choose your audio file', type=["mp3","wav"])
                if uploaded_audio_voice:
                    if uploaded_audio_voice.name.endswith('wav'):
                        audio_new_voice = pydub.AudioSegment.from_wav(uploaded_audio_voice)
                        audio_new_voice.export("audio_new_voice.wav", format="wav")
                        audio_file_voice = open("audio_new_voice.wav", "rb")
                        transcript_voice = genai.speech2text(audio_file_voice)
                        file = ['./audio_new_voice.wav']
                        voice_clone(new_voice_name, 'A custom voice', file)
                        st.write(transcript_voice)
                    else:
                        audio_new_voice = pydub.AudioSegment.from_mp3(uploaded_audio_voice)
                        audio_new_voice.export("audio_new_voice.mp3", format="mp3")
                        audio_file_voice = open("audio_new_voice.mp3", "rb")
                        transcript_voice = genai.speech2text(audio_file_voice)
                        file = ['./audio_new_voice.mp3']
                        voice_clone(new_voice_name, 'A custom voice', file)
                        st.write(transcript_voice)

                submitted_voice = st.form_submit_button("Submit")
                if submitted_voice:
                    st.audio(voice_custom(transcript_voice, voice_name=new_voice_name))
                    st.write(transcript_voice)
