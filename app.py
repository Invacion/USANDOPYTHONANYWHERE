from difflib import SequenceMatcher
import re
import os
from flask import Flask, render_template, request, redirect 
from pydub import AudioSegment
import speech_recognition as sr
from googletrans import Translator  # Importamos el traductor

app = Flask(__name__)

# Carpeta para almacenar los archivos subidos
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Asegúrate de que la carpeta exista
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

def clean_text(text):
    # Eliminar signos de puntuación y convertir a minúsculas
    text = re.sub(r'[^\w\s]', '', text)  # Eliminar todo excepto letras y espacios
    text = text.lower()  # Convertir a minúsculas
    return text

def replace_synonyms(text, synonyms_dict):
    # Reemplazar sinónimos en el texto
    for key, synonyms in synonyms_dict.items():
        for synonym in synonyms:
            text = text.replace(synonym, key)
    return text

def are_synonyms(word1, word2, synonyms_dict):
    # Comprobar si las palabras son sinónimos
    return (word1 in synonyms_dict and word2 in synonyms_dict[word1]) or \
        (word2 in synonyms_dict and word1 in synonyms_dict[word2])

def calculate_difference_and_print_changes(text1, text2, synonyms_dict):
    # Limpiar los textos
    cleaned_text1 = clean_text(text1)
    cleaned_text2 = clean_text(text2)

    # Reemplazar sinónimos en los textos
    cleaned_text1 = replace_synonyms(cleaned_text1, synonyms_dict)
    cleaned_text2 = replace_synonyms(cleaned_text2, synonyms_dict)

    # Dividir los textos en palabras
    words1 = cleaned_text1.split()
    words2 = cleaned_text2.split()

    # Usar SequenceMatcher para calcular las diferencias
    matcher = SequenceMatcher(None, words1, words2)
    differences = matcher.get_opcodes()

    # Calcular el número de diferencias
    num_differences = 0
    changes = []

    for tag, i1, i2, j1, j2 in differences:
        if tag == 'replace':
            # Si hay un reemplazo, imprime las palabras cambiadas
            for i in range(i1, i2):
                # Verificar que j1 no exceda el tamaño de words2
                if j1 < len(words2):
                    if not are_synonyms(words1[i], words2[j1], synonyms_dict):
                        changes.append(f"{words1[i]} --> {words2[j1]}")
                        num_differences += 1
                    j1 += 1  # Incrementar j1 solo si está dentro del rango
        elif tag == 'delete':
            for i in range(i1, i2):
                changes.append(f"{words1[i]} --> (deleted)")
                num_differences += 1
        elif tag == 'insert':
            for j in range(j1, j2):
                # Verificar que j no exceda el tamaño de words2
                if j < len(words2):
                    changes.append(f"(inserted) --> {words2[j]}")
                    num_differences += 1

    # Calcular el porcentaje de diferencia
    total_length = max(len(words1), len(words2))
    if total_length > 0:
        percentage_difference = (num_differences / total_length) * 100
    else:
        percentage_difference = 0.0  # Evitar división por cero

    # Clasificación del porcentaje de cambio
    if percentage_difference == 0:
        change_level = "Excelente 5/5"
    elif percentage_difference <= 20:
        change_level = "Muy bien 4/5"
    elif percentage_difference <= 60:
        change_level = "Bien 3/5"
    elif percentage_difference <= 60:
        change_level = "Satisfactorio 2/5"
    else:
        change_level = "Insuficiente 1/5"  # En caso de que sea más del 60% de diferencia

    return percentage_difference, change_level

# Definir un diccionario de sinónimos
synonyms_dict = {
    "i am": ["im", "i'm"],
    "im": ["i am", "i'm"],
    "happy": ["glad", "joyful"],
    "it is": ["its"],
    "is": ["its"],
    "it": ["is"],
    "quarter": ["room", "section", "part", "area"],
    "okey": ["well", "alright", "fine"],
    "okay": ["okey", "alright", "fine"],            
    "i am": ["im", "i'm"],
    "im": ["i am", "i'm"],
    "i'm": ["i am", "im"],
    "sad": ["unhappy", "sorrowful", "down", "blue", "melancholy"],
    "happy": ["glad", "joyful", "cheerful", "content", "pleased"],
    "big": ["large", "huge", "gigantic", "enormous", "vast"],
    "small": ["tiny", "miniature", "petite", "compact", "little"],
    "fast": ["quick", "swift", "rapid", "speedy", "hasty"],
    "slow": ["leisurely", "unhurried", "delayed", "gradual", "sluggish"],
    "good": ["great", "excellent", "fantastic", "wonderful", "nice"],
    "bad": ["poor", "terrible", "awful", "horrible", "dreadful"],
    "strong": ["powerful", "robust", "tough", "sturdy", "solid"],
    "weak": ["fragile", "delicate", "frail", "feeble", "soft"],
    "beautiful": ["attractive", "pretty", "lovely", "gorgeous", "stunning"],
    "ugly": ["unattractive", "hideous", "unsightly", "ugliness", "repulsive"],
    "smart": ["intelligent", "clever", "bright", "wise", "sharp"],
    "dumb": ["stupid", "unintelligent", "ignorant", "foolish", "slow-witted"],
    "strong": ["muscular", "powerful", "tough", "mighty"],
    "weak": ["fragile", "delicate", "frail", "soft"],
    "rich": ["wealthy", "affluent", "prosperous", "well-off"],
    "poor": ["broke", "impoverished", "needy", "destitute", "underprivileged"],
    "old": ["ancient", "elderly", "aged", "vintage", "senior"],
    "young": ["youthful", "new", "teenage", "juvenile", "fresh"],
    "hard": ["difficult", "challenging", "tough", "arduous", "strenuous"],
    "easy": ["simple", "effortless", "straightforward", "light", "manageable"],
    "quick": ["fast", "swift", "rapid", "speedy", "brisk"],
    "slow": ["delayed", "sluggish", "unhurried", "gradual"],
    "hot": ["warm", "scorching", "boiling", "sizzling", "heated"],
    "cold": ["chilly", "frigid", "cool", "frosty", "icy"],
    "angry": ["furious", "irritated", "mad", "enraged", "upset"],
    "calm": ["peaceful", "relaxed", "composed", "serene", "tranquil"],
    "clean": ["tidy", "neat", "organized", "spotless", "sanitary"],
    "dirty": ["unclean", "messy", "filthy", "grimy", "soiled"],
    "friendly": ["amiable", "sociable", "pleasant", "cordial", "companionable"],
    "unfriendly": ["hostile", "cold", "aloof", "distant", "antagonistic"],
    "strong": ["powerful", "robust", "tough", "mighty", "muscular"],
    "weak": ["fragile", "delicate", "frail", "soft", "feeble"]
}

# Función para obtener la duración del archivo de audio
def get_audio_duration(filepath):
    # Cargar el archivo de audio
    audio = AudioSegment.from_file(filepath)
    # Obtener la duración en segundos
    duration_seconds = len(audio) / 1000.0  # Pydub da la duración en milisegundos, lo convertimos a segundos
    return duration_seconds

# Función para calcular la fluidez
def calculate_fluency(transcription, audio_filepath):
    # Contamos el número de palabras en la transcripción
    num_words = len(transcription.split())

    # Obtener la duración del audio
    audio_duration = get_audio_duration(audio_filepath)

    # Convertir la duración del audio a minutos
    audio_duration_minutes = audio_duration / 60.0

    # Calcular la fluidez en palabras por minuto
    if audio_duration_minutes > 0:
        fluency = num_words / audio_duration_minutes
    else:
        fluency = 0

    # Calificar la fluidez
    if fluency >= 50:
        fluency_level = "Excelente 5/5"
    elif fluency >= 40:
        fluency_level = "Muy bien 4/5"
    elif fluency >= 30:
        fluency_level = "Bien 3/5"
    elif fluency >= 10:
        fluency_level = "Satisfactorio 2/5"
    else:
        fluency_level = "Insuficiente 1/5"  # En caso de que haya menos de 10 palabras por minuto

    return fluency, fluency_level

@app.route('/upload', methods=['POST'])
def upload_file():
    # Verificar si se subió un archivo
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        return redirect(request.url)

    if file:
        
        if not file.filename.endswith('.wav'):
            error_message = "Solo se permiten archivos WAV"
            return render_template('index.html', error_message=error_message)


        # Guardar el archivo subido en la carpeta 'uploads'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # Transcribir el audio
        transcription = transcribe_audio(filepath)

        # Traducir el texto al español y luego al inglés
        translated_text = translate_text(transcription)

        # Calcular el porcentaje de diferencia y las palabras cambiadas
        percentage_difference, changes = calculate_difference_and_print_changes(
            transcription, translated_text['english'], synonyms_dict
        )

        # Calcular la fluidez
        fluency = calculate_fluency(transcription, filepath)

        # Pasar la transcripción, las traducciones, el porcentaje de diferencia, los cambios y la fluidez a la plantilla 'result.html'
        return render_template('result.html', transcription=transcription, 
                               translated_text=translated_text, 
                               change_percentage=percentage_difference,
                               changes=changes, fluency=fluency)

def calculate_changes_percentage(original_text, translated_text):
    # Usamos difflib para comparar los dos textos
    sequence_matcher = SequenceMatcher(None, original_text, translated_text)
    # Calculamos la proporción de similitud
    similarity = sequence_matcher.ratio()
    # Calculamos el porcentaje de diferencia
    change_percentage = (1 - similarity) * 100
    return change_percentage

def transcribe_audio(filepath):
    recognizer = sr.Recognizer()
    audio_file = sr.AudioFile(filepath)

    with audio_file as source:
        audio = recognizer.record(source)  # Graba todo el contenido del archivo

    try:
        # Usamos el reconocimiento de Google para transcribir el audio
        transcription = recognizer.recognize_google(audio, language="en-US")
        print("Texto transcrito:", transcription)

        # Llamamos a la función para agregar signos de interrogación y puntos
        result = add_question_marks(transcription)
        print("Texto corregido v2:", result) 
        return result

    except sr.UnknownValueError:
        return "No se pudo entender el audio."
    except sr.RequestError:
        return "Hubo un error al contactar el servicio de transcripción."

def translate_text(text):
    translator = Translator()

    # Traducir el texto al español
    translated_to_spanish = translator.translate(text, src='en', dest='es').text
    print("Texto traducido al español:", translated_to_spanish)

    # Traducir el texto al inglés
    translated_to_english = translator.translate(translated_to_spanish, src='es', dest='en').text
    print("Texto traducido al inglés:", translated_to_english)

    return {'spanish': translated_to_spanish, 'english': translated_to_english}

def add_question_marks(text):
    question_words_combinations = [
        ("who", ["is", "was", "are", "were", "did", "does"]),
        ("what", ["is", "time", "are", "was", "were", "do", "does", "goes", "works"]),
        ("where", ["is", "are", "does", "was", "were"]),
        ("when", ["is", "was", "are", "were"]),
        ("why", ["is", "are", "do", "does", "was", "were", "I", "you", "he", "she", "it"]),
        ("how", ["is", "are", "do", "does", "was", "were", "many", "much"]),
        ("which", ["is", "are", "was", "were"]),
        ("whom", ["did", "does", "is", "was"]),
        ("whose", ["is", "are"]),
        ("how many", ["is", "are", "do", "does"]),
        ("how much", ["is", "are", "does", "do"]),
        ("how long", ["is", "are", "do", "does"]),
        ("how far", ["is", "are", "do", "does"]),
        ("how often", ["do", "does", "is", "are"]),
        ("how old", ["is", "are"]),
        ("how come", ["is", "are", "did"]),
        ("what time", ["is", "does"]),
        ("what kind", ["is", "are"]),
        ("what else", ["is", "are"]),
        ("what about", ["is", "are"]),
        ("who else", ["is", "are"]),
        ("who did", ["it", "you", "they"]),
        ("who was", ["it", "he", "she"]),
        ("who is", ["it", "he", "she"]),
        ("will", ["I", "you", "he", "she", "we", "they"]),
        ("can", ["I", "you", "he", "she", "we", "they"]),
        ("could", ["I", "you", "he", "she", "we", "they"]),
        ("would", ["I", "you", "he", "she", "we", "they"]),
        ("do", ["I", "you", "he", "she", "it", "we", "they"]),
        ("does", ["he", "she", "it"]),
        ("did", ["I", "you", "he", "she", "it", "we", "they"]),
        
        ("is", ["he", "she", "it"]),
        ("are", ["you", "we", "they"]),
        ("am", ["I"]),
        
        ("was", ["I", "he", "she", "it"]),
        ("were", ["you", "we", "they"]),
        ("has", ["he", "she", "it"]),
        ("have", ["I", "you", "we", "they"]),
        ("had", ["I", "you", "he", "she", "it", "we", "they"]),
        ("may", ["I", "you", "he", "she", "it", "we", "they"]),
        ("might", ["I", "you", "he", "she", "it", "we", "they"]),
        ("shall", ["I", "we"]),
        ("should", ["I", "you", "he", "she", "it", "we", "they"]),
        ("must", ["I", "you", "he", "she", "it", "we", "they"])
    ]

    # Lista de pronombres y sus combinaciones
    pronouns_combinations = [
        ("I", ["do", "don't", "am", "always", "usually", "frequently", "often", "sometimes", "occasionally", "rarely", "seldom", "never", "go", "work", "eat", "sleep", "play", "read", "write", "speak", "study", "run", "walk", "talk", "watch", "listen", "understand", "want", "need", "like", "love", "hate", "believe", "think", "help", "ask", "answer", "try", "enjoy", "hope", "feel", "wait", "bring", "carry", "drive", "buy", "sell", "teach", "learn", "see", "hear", "feel", "hold", "build", "workout", "cook", "travel", "stay", "live", "grow", "clean", "paint", "dance", "sing", "jump", "swim", "call", "play", "study", "remember", "forget", "understand", "buy", "pay", "open", "close", "set", "build", "work", "finish", "start", "move", "turn", "use", "create", "call", "help", "try", "play", "drive", "run", "watch", "choose", "change", "build", "draw", "train", "know", "push", "shut", "read", "accept", "push", "call", "help", "talk", "walk", "wear", "watch", "work", "have", "live", "create", "work", "write", "love", "wish", "understand", "open", "study", "sleep", "teach", "eat", "speak", "play", "finish", "stop", "hold", "wait", "run", "move", "turn", "read", "bring", "finish", "help", "play", "stay", "push", "take", "drive", "take", "start", "understand", "learn", "finish", "grow", "clean", "send", "stop", "talk", "sing", "write", "climb", "jump", "dance", "help", "play", "open", "close", "work", "have", "bring", "try", "help", "take", "get", "take", "run", "change", "work", "move", "turn", "get", "need", "believe", "wish", "live", "see", "watch", "listen", "draw", "speak", "try", "answer", "speak", "play", "study", "like"]),
        ("you", ["do", "don't", "are", "always", "usually", "frequently", "often", "sometimes", "occasionally", "rarely", "seldom", "never", "go", "work", "eat", "sleep", "play", "read", "write", "speak", "study", "run", "walk", "talk", "watch", "listen", "understand", "want", "need", "like", "love", "hate", "believe", "think", "help", "ask", "answer", "try", "enjoy", "hope", "feel", "wait", "bring", "carry", "drive", "buy", "sell", "teach", "learn", "see", "hear", "feel", "hold", "build", "workout", "cook", "travel", "stay", "live", "grow", "clean", "paint", "dance", "sing", "jump", "swim", "call", "play", "study", "remember", "forget", "understand", "buy", "pay", "open", "close", "set", "build", "work", "finish", "start", "move", "turn", "use", "create", "call", "help", "try", "play", "drive", "run", "watch", "choose", "change", "build", "draw", "train", "know", "push", "shut", "read", "accept", "push", "call", "help", "talk", "walk", "wear", "watch", "work", "have", "live", "create", "work", "write", "love", "wish", "understand", "open", "study", "sleep", "teach", "eat", "speak", "play", "finish", "stop", "hold", "wait", "run", "move", "turn", "read", "bring", "finish", "help", "play", "stay", "push", "take", "drive", "take", "start", "understand", "learn", "finish", "grow", "clean", "send", "stop", "talk", "sing", "write", "climb", "jump", "dance", "help", "play", "open", "close", "work", "have", "bring", "try", "help", "take", "get", "take", "run", "change", "work", "move", "turn", "get", "need", "believe", "wish", "live", "see", "watch", "listen", "draw", "speak", "try", "answer", "speak", "play", "study", "like"]),
        ("we", ["do", "don't", "are", "always", "usually", "frequently", "often", "sometimes", "occasionally", "rarely", "seldom", "never", "go", "work", "eat", "sleep", "play", "read", "write", "speak", "study", "run", "walk", "talk", "watch", "listen", "understand", "want", "need", "like", "love", "hate", "believe", "think", "help", "ask", "answer", "try", "enjoy", "hope", "feel", "wait", "bring", "carry", "drive", "buy", "sell", "teach", "learn", "see", "hear", "feel", "hold", "build", "workout", "cook", "travel", "stay", "live", "grow", "clean", "paint", "dance", "sing", "jump", "swim", "call", "play", "study", "remember", "forget", "understand", "buy", "pay", "open", "close", "set", "build", "work", "finish", "start", "move", "turn", "use", "create", "call", "help", "try", "play", "drive", "run", "watch", "choose", "change", "build", "draw", "train", "know", "push", "shut", "read", "accept", "push", "call", "help", "talk", "walk", "wear", "watch", "work", "have", "live", "create", "work", "write", "love", "wish", "understand", "open", "study", "sleep", "teach", "eat", "speak", "play", "finish", "stop", "hold", "wait", "run", "move", "turn", "read", "bring", "finish", "help", "play", "stay", "push", "take", "drive", "take", "start", "understand", "learn", "finish", "grow", "clean", "send", "stop", "talk", "sing", "write", "climb", "jump", "dance", "help", "play", "open", "close", "work", "have", "bring", "try", "help", "take", "get", "take", "run", "change", "work", "move", "turn", "get", "need", "believe", "wish", "live", "see", "watch", "listen", "draw", "speak", "try", "answer", "speak", "play", "study", "like"]),
        ("they", ["do", "don't", "are", "always", "usually", "frequently", "often", "sometimes", "occasionally", "rarely", "seldom", "never", "go", "work", "eat", "sleep", "play", "read", "write", "speak", "study", "run", "walk", "talk", "watch", "listen", "understand", "want", "need", "like", "love", "hate", "believe", "think", "help", "ask", "answer", "try", "enjoy", "hope", "feel", "wait", "bring", "carry", "drive", "buy", "sell", "teach", "learn", "see", "hear", "feel", "hold", "build", "workout", "cook", "travel", "stay", "live", "grow", "clean", "paint", "dance", "sing", "jump", "swim", "call", "play", "study", "remember", "forget", "understand", "buy", "pay", "open", "close", "set", "build", "work", "finish", "start", "move", "turn", "use", "create", "call", "help", "try", "play", "drive", "run", "watch", "choose", "change", "build", "draw", "train", "know", "push", "shut", "read", "accept", "push", "call", "help", "talk", "walk", "wear", "watch", "work", "have", "live", "create", "work", "write", "love", "wish", "understand", "open", "study", "sleep", "teach", "eat", "speak", "play", "finish", "stop", "hold", "wait", "run", "move", "turn", "read", "bring", "finish", "help", "play", "stay", "push", "take", "drive", "take", "start", "understand", "learn", "finish", "grow", "clean", "send", "stop", "talk", "sing", "write", "climb", "jump", "dance", "help", "play", "open", "close", "work", "have", "bring", "try", "help", "take", "get", "take", "run", "change", "work", "move", "turn", "get", "need", "believe", "wish", "live", "see", "watch", "listen", "draw", "speak", "try", "answer", "speak", "play", "study", "like"]),
       
        ("she", ["does", "doesn't", "is", "always", "usually", "frequently", "often", "sometimes", "occasionally", "rarely", "seldom", "never", "goes", "works", "eats", "sleeps", "plays", "reads", "writes", "speaks", "studies", "runs", "walks", "talks", "watches", "listens", "understands", "wants", "needs", "likes", "loves", "hates", "believes", "thinks", "helps", "asks", "answers", "tries", "enjoys", "hopes", "feels", "waits", "brings", "carries", "drives", "buys", "sells", "teaches", "learns", "sees", "hears", "holds", "builds", "works out", "cooks", "travels", "stays", "lives", "grows", "cleans", "paints", "dances", "sings", "jumps", "swims", "calls", "plays", "studies", "remembers", "forgets", "understands", "pays", "opens", "closes", "sets", "finishes", "starts", "moves", "turns", "uses", "creates", "chooses", "changes", "draws", "trains", "knows", "pushes", "shuts", "accepts", "talks", "walks", "wears", "has", "creates", "writes", "wishes", "opens", "sleeps", "teaches", "eats", "speaks", "finishes", "stops", "holds", "waits", "runs", "moves", "turns", "brings", "stays", "takes", "drives", "starts", "learns", "grows", "cleans", "sends", "talks", "sings", "climbs", "plays", "opens", "closes", "has", "brings", "takes", "gets", "runs", "changes", "moves", "needs", "believes", "sees", "watches", "listens", "draws", "speaks", "answers", "studies", "likes"]),
        ("he", ["does", "doesn't", "is", "always", "usually", "frequently", "often", "sometimes", "occasionally", "rarely", "seldom", "never", "goes", "works", "eats", "sleeps", "plays", "reads", "writes", "speaks", "studies", "runs", "walks", "talks", "watches", "listens", "understands", "wants", "needs", "likes", "loves", "hates", "believes", "thinks", "helps", "asks", "answers", "tries", "enjoys", "hopes", "feels", "waits", "brings", "carries", "drives", "buys", "sells", "teaches", "learns", "sees", "hears", "holds", "builds", "works out", "cooks", "travels", "stays", "lives", "grows", "cleans", "paints", "dances", "sings", "jumps", "swims", "calls", "plays", "studies", "remembers", "forgets", "understands", "pays", "opens", "closes", "sets", "finishes", "starts", "moves", "turns", "uses", "creates", "chooses", "changes", "draws", "trains", "knows", "pushes", "shuts", "accepts", "talks", "walks", "wears", "has", "creates", "writes", "wishes", "opens", "sleeps", "teaches", "eats", "speaks", "finishes", "stops", "holds", "waits", "runs", "moves", "turns", "brings", "stays", "takes", "drives", "starts", "learns", "grows", "cleans", "sends", "talks", "sings", "climbs", "plays", "opens", "closes", "has", "brings", "takes", "gets", "runs", "changes", "moves", "needs", "believes", "sees", "watches", "listens", "draws", "speaks", "answers", "studies", "likes"]),
        ("it", [ "is", "doesn't", "always", "usually", "frequently", "often", "sometimes", "occasionally", "rarely", "seldom", "never", "goes", "works", "eats", "sleeps", "plays", "reads", "writes", "speaks", "studies", "runs", "walks", "talks", "watches", "listens", "understands", "wants", "needs", "likes", "loves", "hates", "believes", "thinks", "helps", "asks", "answers", "tries", "enjoys", "hopes", "feels", "waits", "brings", "carries", "drives", "buys", "sells", "teaches", "learns", "sees", "hears", "holds", "builds", "works out", "cooks", "travels", "stays", "lives", "grows", "cleans", "paints", "dances", "sings", "jumps", "swims", "calls", "plays", "studies", "remembers", "forgets", "understands", "pays", "opens", "closes", "sets", "finishes", "starts", "moves", "turns", "uses", "creates", "chooses", "changes", "draws", "trains", "knows", "pushes", "shuts", "accepts", "talks", "walks", "wears", "has", "creates", "writes", "wishes", "opens", "sleeps", "teaches", "eats", "speaks", "finishes", "stops", "holds", "waits", "runs", "moves", "turns", "brings", "stays", "takes", "drives", "starts", "learns", "grows", "cleans", "sends", "talks", "sings", "climbs", "plays", "opens", "closes", "has", "brings", "takes", "gets", "runs", "changes", "moves", "needs", "believes", "sees", "watches", "listens", "draws", "speaks", "answers", "studies", "likes"]),
       
        ("I'm", ["going", "working", "eating", "sleeping", "playing", "reading", "writing", "speaking", "studying", "running", "walking", "talking", "watching", "listening", "understanding", "wanting", "needing", "liking", "loving", "hating", "believing", "thinking", "helping", "asking", "answering", "trying", "enjoying", "hoping", "feeling", "waiting", "bringing", "carrying", "driving", "buying", "selling", "teaching", "learning", "seeing", "hearing", "holding", "building", "working out", "cooking", "traveling", "staying", "living", "growing", "cleaning", "painting", "dancing", "singing", "jumping", "swimming", "calling", "studying", "remembering", "forgetting", "understanding", "paying", "opening", "closing", "setting", "finishing", "starting", "moving", "turning", "using", "creating", "helping", "driving", "choosing", "changing", "drawing", "training", "knowing", "pushing", "shutting", "accepting", "talking", "wearing", "having", "loving", "wishing", "studying", "sleeping", "teaching", "speaking", "stopping", "holding", "waiting", "taking", "getting", "running", "changing", "finishing", "sending", "climbing", "jumping", "dancing", "playing", "opening", "closing", "trying", "helping", "taking", "getting", "moving", "turning", "needing", "believing", "watching", "listening", "drawing", "answering", "studying", "liking"]),
        ("you're", ["welcome", "going", "working", "eating", "sleeping", "playing", "reading", "writing", "speaking", "studying", "running", "walking", "talking", "watching", "listening", "understanding", "wanting", "needing", "liking", "loving", "hating", "believing", "thinking", "helping", "asking", "answering", "trying", "enjoying", "hoping", "feeling", "waiting", "bringing", "carrying", "driving", "buying", "selling", "teaching", "learning", "seeing", "hearing", "holding", "building", "working out", "cooking", "traveling", "staying", "living", "growing", "cleaning", "painting", "dancing", "singing", "jumping", "swimming", "calling", "studying", "remembering", "forgetting", "understanding", "paying", "opening", "closing", "setting", "finishing", "starting", "moving", "turning", "using", "creating", "helping", "driving", "choosing", "changing", "drawing", "training", "knowing", "pushing", "shutting", "accepting", "talking", "wearing", "having", "loving", "wishing", "studying", "sleeping", "teaching", "speaking", "stopping", "holding", "waiting", "taking", "getting", "running", "changing", "finishing", "sending", "climbing", "jumping", "dancing", "playing", "opening", "closing", "trying", "helping", "taking", "getting", "moving", "turning", "needing", "believing", "watching", "listening", "drawing", "answering", "studying", "liking"]),
        ("we're", ["going", "working", "eating", "sleeping", "playing", "reading", "writing", "speaking", "studying", "running", "walking", "talking", "watching", "listening", "understanding", "wanting", "needing", "liking", "loving", "hating", "believing", "thinking", "helping", "asking", "answering", "trying", "enjoying", "hoping", "feeling", "waiting", "bringing", "carrying", "driving", "buying", "selling", "teaching", "learning", "seeing", "hearing", "holding", "building", "working out", "cooking", "traveling", "staying", "living", "growing", "cleaning", "painting", "dancing", "singing", "jumping", "swimming", "calling", "studying", "remembering", "forgetting", "understanding", "paying", "opening", "closing", "setting", "finishing", "starting", "moving", "turning", "using", "creating", "helping", "driving", "choosing", "changing", "drawing", "training", "knowing", "pushing", "shutting", "accepting", "talking", "wearing", "having", "loving", "wishing", "studying", "sleeping", "teaching", "speaking", "stopping", "holding", "waiting", "taking", "getting", "running", "changing", "finishing", "sending", "climbing", "jumping", "dancing", "playing", "opening", "closing", "trying", "helping", "taking", "getting", "moving", "turning", "needing", "believing", "watching", "listening", "drawing", "answering", "studying", "liking"]),
        ("they're", ["going", "working", "eating", "sleeping", "playing", "reading", "writing", "speaking", "studying", "running", "walking", "talking", "watching", "listening", "understanding", "wanting", "needing", "liking", "loving", "hating", "believing", "thinking", "helping", "asking", "answering", "trying", "enjoying", "hoping", "feeling", "waiting", "bringing", "carrying", "driving", "buying", "selling", "teaching", "learning", "seeing", "hearing", "holding", "building", "working out", "cooking", "traveling", "staying", "living", "growing", "cleaning", "painting", "dancing", "singing", "jumping", "swimming", "calling", "studying", "remembering", "forgetting", "understanding", "paying", "opening", "closing", "setting", "finishing", "starting", "moving", "turning", "using", "creating", "helping", "driving", "choosing", "changing", "drawing", "training", "knowing", "pushing", "shutting", "accepting", "talking", "wearing", "having", "loving", "wishing", "studying", "sleeping", "teaching", "speaking", "stopping", "holding", "waiting", "taking", "getting", "running", "changing", "finishing", "sending", "climbing", "jumping", "dancing", "playing", "opening", "closing", "trying", "helping", "taking", "getting", "moving", "turning", "needing", "believing", "watching", "listening", "drawing", "answering", "studying", "liking"]),
        ("she's", ["going", "working", "eating", "sleeping", "playing", "reading", "writing", "speaking", "studying", "running", "walking", "talking", "watching", "listening", "understanding", "wanting", "needing", "liking", "loving", "hating", "believing", "thinking", "helping", "asking", "answering", "trying", "enjoying", "hoping", "feeling", "waiting", "bringing", "carrying", "driving", "buying", "selling", "teaching", "learning", "seeing", "hearing", "holding", "building", "working out", "cooking", "traveling", "staying", "living", "growing", "cleaning", "painting", "dancing", "singing", "jumping", "swimming", "calling", "studying", "remembering", "forgetting", "understanding", "paying", "opening", "closing", "setting", "finishing", "starting", "moving", "turning", "using", "creating", "helping", "driving", "choosing", "changing", "drawing", "training", "knowing", "pushing", "shutting", "accepting", "talking", "wearing", "having", "loving", "wishing", "studying", "sleeping", "teaching", "speaking", "stopping", "holding", "waiting", "taking", "getting", "running", "changing", "finishing", "sending", "climbing", "jumping", "dancing", "playing", "opening", "closing", "trying", "helping", "taking", "getting", "moving", "turning", "needing", "believing", "watching", "listening", "drawing", "answering", "studying", "liking"]),
        ("he's", ["going", "working", "eating", "sleeping", "playing", "reading", "writing", "speaking", "studying", "running", "walking", "talking", "watching", "listening", "understanding", "wanting", "needing", "liking", "loving", "hating", "believing", "thinking", "helping", "asking", "answering", "trying", "enjoying", "hoping", "feeling", "waiting", "bringing", "carrying", "driving", "buying", "selling", "teaching", "learning", "seeing", "hearing", "holding", "building", "working out", "cooking", "traveling", "staying", "living", "growing", "cleaning", "painting", "dancing", "singing", "jumping", "swimming", "calling", "studying", "remembering", "forgetting", "understanding", "paying", "opening", "closing", "setting", "finishing", "starting", "moving", "turning", "using", "creating", "helping", "driving", "choosing", "changing", "drawing", "training", "knowing", "pushing", "shutting", "accepting", "talking", "wearing", "having", "loving", "wishing", "studying", "sleeping", "teaching", "speaking", "stopping", "holding", "waiting", "taking", "getting", "running", "changing", "finishing", "sending", "climbing", "jumping", "dancing", "playing", "opening", "closing", "trying", "helping", "taking", "getting", "moving", "turning", "needing", "believing", "watching", "listening", "drawing", "answering", "studying", "liking"]),
        ("it's", ["going", "a", "working", "eating", "sleeping", "playing", "reading", "writing", "speaking", "studying", "running", "walking", "talking", "watching", "listening", "understanding", "wanting", "needing", "liking", "loving", "hating", "believing", "thinking", "helping", "asking", "answering", "trying", "enjoying", "hoping", "feeling", "waiting", "bringing", "carrying", "driving", "buying", "selling", "teaching", "learning", "seeing", "hearing", "holding", "building", "working out", "cooking", "traveling", "staying", "living", "growing", "cleaning", "painting", "dancing", "singing", "jumping", "swimming", "calling", "studying", "remembering", "forgetting", "understanding", "paying", "opening", "closing", "setting", "finishing", "starting", "moving", "turning", "using", "creating", "helping", "driving", "choosing", "changing", "drawing", "training", "knowing", "pushing", "shutting", "accepting", "talking", "wearing", "having", "loving", "wishing", "studying", "sleeping", "teaching", "speaking", "stopping", "holding", "waiting", "taking", "getting", "running", "changing", "finishing", "sending", "climbing", "jumping", "dancing", "playing", "opening", "closing", "trying", "helping", "taking", "getting", "moving", "turning", "needing", "believing", "watching", "listening", "drawing", "answering", "studying", "liking"]),
        ("thank", ["you"]),
        ("thanks", ["so"]),
        ("see", ["you soon", "you tomorrow", "you again"]),  
        ("thanks", ["so", "for"]),
        ("bye", ["bye"]),   
        ("yes", ["I", "you", "we", "they", "she", "he", "it"]),
        ("no", ["I", "you", "we", "they", "she", "he", "it"]), 
        ("if", ["I", "you", "we", "they", "she", "he", "it"]),    
        
        ("the", ["book", "car", "house", "dog", "cat", "computer", "idea", "movie", "tree", "person", "problem", "question", "answer", "day", "night", "city", "town", "place", "school", "work", "friend", "family", "room", "party", "team", "teacher", "student", "company", "office", "restaurant", "game", "song", "event", "planet", "country", "continent", "mountain", "river", "lake", "ocean", "beach", "forest", "desert", "house", "street", "building", "shop", "store", "factory", "station", "bus", "train", "plane", "bike", "club", "service", "market", "home", "idea", "show", "problem", "discussion", "friendship", "relationship", "experience", "situation", "feeling", "thing", "place", "world", "universe", "moon", "star", "holiday", "celebration", "moment", "time", "space", "goal", "project", "plan", "dream", "wish", "challenge", "task", "plan", "activity", "journey", "experience", "opportunity", "idea", "meeting", "concept", "opinion", "thought", "discussion", "memory", "vision", "action", "decision", "topic", "news", "item", "object", "subject", "question", "answer", "result", "aspect", "case", "event", "strategy", "factor", "method", "technique", "idea", "argument", "resource", "role", "plan", "strategy", "solution", "problem", "debate", "point", "opinion", "reason", "goal", "wish", "success", "failure", "test", "exam", "study", "subject", "review", "review", "problem", "books", "cars", "houses", "dogs", "cats", "computers", "ideas", "movies", "trees", "persons", "problems", "questions", "answers", "days", "nights", "cities", "towns", "places", "schools", "works", "friends", "families", "rooms", "parties", "teams", "teachers", "students", "companies", "offices", "restaurants", "games", "songs", "events", "planets", "countries", "continents", "mountains", "rivers", "lakes", "oceans", "beaches", "forests", "deserts", "streets", "buildings", "shops", "stores", "factories", "stations", "buses", "trains", "planes", "bikes", "clubs", "services", "markets", "homes", "shows", "problems", "discussions", "friendships", "relationships", "experiences", "situations", "feelings", "things", "worlds", "universes", "moons", "stars", "holidays", "celebrations", "moments", "times", "spaces", "goals", "projects", "plans", "dreams", "wishes", "challenges", "tasks", "activities", "journeys", "opportunities", "meetings", "concepts", "opinions", "thoughts", "memories", "visions", "actions", "decisions", "topics", "news", "items", "objects", "subjects", "questions", "answers", "results", "aspects", "cases", "strategies", "factors", "methods", "techniques", "arguments", "resources", "roles", "solutions", "debates", "points", "reasons", "successes", "failures", "tests", "exams", "studies", "subjects", "reviews"])  
    ]

    # Construir la expresión regular a partir de la lista de combinaciones de pronombres
    pronouns_pattern = "|".join([f"\\b{pronoun} ({'|'.join(combinations)})" for pronoun, combinations in pronouns_combinations])

    # Extraer las palabras de pregunta de la lista de combinaciones
    question_words = [pair[0] for pair in question_words_combinations]
    question_words_pattern = "|".join(question_words)

    # Primero agregamos signos de interrogación donde corresponde
    match = re.search(rf"({question_words_pattern})(.*?)(\b{pronouns_pattern}\b)", text)

    if match:
        # Buscar el índice en el que comienza el pronombre
        pronoun_start_index = match.start(3)

        # Verificar que el índice se haya encontrado
        if pronoun_start_index != -1:
            # Buscar el índice antes de un espacio antes del pronombre
            question_mark_position = pronoun_start_index - 1

            # Insertar el signo de interrogación justo antes del pronombre
            modified_text = text[:question_mark_position] + "?" + text[question_mark_position:]
            return modified_text  # Retornar el texto modificado
        else:
            return text
    else:
        # Buscar las palabras de pregunta al principio de la oración sin pronombres
        question_match = re.search(rf"({question_words_pattern})\b(.*)", text)

        if question_match:
            question_word = question_match.group(1)
            rest_of_text = question_match.group(2).strip()

            # Si no hay un pronombre después de la palabra de pregunta
            if not re.search(pronouns_pattern, rest_of_text):
                # Agregar el signo de interrogación al final
                text = text + "?"
            else:
                # Si ya hay un pronombre, dejamos el texto igual
                return text

    # Añadir puntos en otros lugares donde corresponda
    for pronoun, combinations in pronouns_combinations:
        for combination in combinations:
            # Buscar coincidencias de pronombre + verbo
            text = re.sub(rf"(\b{pronoun} {combination}\b)(?!\?)", r". \1", text)

    # Añadir un solo punto antes de la palabra de pregunta, si no está precedida de uno
    text = re.sub(rf"(?<!\.)\s*(?=\b{question_words_pattern}\b)", ".", text)

    # Reemplazar puntos consecutivos por un solo punto
    text = re.sub(r"\.\.+", ".", text)

    # Asegurar que haya un espacio después de cada punto
    text = re.sub(r"(\.)(?=\S)", r". ", text)

    # Eliminar espacios innecesarios antes del punto
    text = re.sub(r"\s+\.", ".", text)

    # Eliminar punto al inicio si existe
    text = text.lstrip(".").lstrip()
    
    return text

