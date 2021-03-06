#Install the  required module using -> pip install -r requirements.txt
import re
import logging
import requests
import urllib
from youtube_transcript_api import YouTubeTranscriptApi
##uncomment this after filling the .env folder
#from dotenv import load_dotenv 
import os

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    ParseMode
)

from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    Filters,
    PicklePersistence,
    CallbackContext
)

from telegram.utils.helpers import escape_markdown
##uncomment this after filling the .env folder
#load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s]%(asctime)s - %(message)s"
)

log = logging.getLogger("YoutubeTranscript")
log.info("\n\n Bot is Starting......")

CHOOSING, SENDING_YOUTUBE_URL, CHOOSING_LANGUAGE, CHOOSING_FORMAT, TRANSLATE, AGE_RISTRICTED = range(
    6)

choose_button = [
    ["👻 Extract subtitle", "ℹ️ Help", "👋Done"]
]

choose_button_markup = ReplyKeyboardMarkup(
    choose_button, resize_keyboard=True, One_time_keyboard=True)


def is_url(text):
    youtube_link_pattern = r"((?:(?:https?:\/\/)(?:www)?\.?(?:youtu\.?be)(?:\.com)?\/(?:.*[=/])*)([^= &?/\r\n]{8,11}))"
    link = re.match(youtube_link_pattern, text)
    if link:
        return link.group(2)
    return None


def no_of_subtitle(video_id, update):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    except:
        update.message.reply_text("No subtitle available for this video",
                                  reply_markup=choose_button_markup)
        return CHOOSING
    language_button = []
    language_dictionary = {}
    for subtitle in transcript_list:
        language = subtitle.language
        language_code = subtitle.language_code
        language_dictionary[language] = language_code
        button = [InlineKeyboardButton(
            text=language, callback_data=language)]
        language_button.append(button)
    language_button.append(
        [InlineKeyboardButton(text="Translate", callback_data="Translate")])
    return InlineKeyboardMarkup(language_button), language_dictionary


def make_timestamp(time, user_format):
    time = float(time)
    hours, remainder = divmod(time, 3600)
    mins, secs = divmod(remainder, 60)
    ms = int(round((time - int(time))*1000, 2))
    secs = int(secs)
    if user_format == "VTT":
        return "{:02.0f}:{:02.0f}:{:02.0f}.{:03d}".format(hours, mins, secs, ms)
    elif user_format == "SRT":
        return "{:02.0f}:{:02.0f}:{:02.0f},{:03d}".format(hours, mins, secs, ms)


def create_file(formated_string, user_format, user_chat_id):
    with open(f"{user_chat_id}.{user_format}", "w", encoding="utf-8") as file:
        file.write(formated_string)


def video_title(video_id):
    params = {"format": "json",
              "url": "https://www.youtube.com/watch?v=%s" % video_id}
    url = "https://www.youtube.com/oembed"
    query_string = urllib.parse.urlencode(params)
    url = url + "?" + query_string
    response = requests.get(url)
    data = response.json()
    return data["title"]


def button_formater(button_list):
    no_of_buttons = len(button_list)
    button_page = {}
    page_no = 1
    for i in range(0, no_of_buttons, 5):
        new_button_list = button_list[i:i+5]
        new_button_list.append([InlineKeyboardButton(
            text="<<", callback_data="<<"), InlineKeyboardButton(text=">>", callback_data=">>")])
        button_page[page_no] = new_button_list
        page_no += 1

    return button_page, page_no


def start(update: Update, context: CallbackContext):
    update.message.reply_text(text=f"🙋*Hello* {escape_markdown(update.effective_user.first_name,version=2)},\n"
                              "☑️*Click on Extract subtitle to Extract subtitle*\n"
                              "☑️*Click on Help if you need help regarding any error that you are geting while using this bot*",
                              reply_markup=choose_button_markup,
                              parse_mode=ParseMode.MARKDOWN_V2)
    return CHOOSING


def choosing(update: Update, context: CallbackContext):
    choice_text = update.message.text
    if choice_text == "Extract subtitle" or choice_text == "👻 Extract subtitle" or choice_text == "extract subtitle":
        update.message.reply_text(
            text="⏩*Send me any youtube video 🔗url that contain subtitle\(Mannual/Generated\):*",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.MARKDOWN_V2)
        return SENDING_YOUTUBE_URL
    if choice_text == "ℹ️ Help" or choice_text == "Help" or choice_text == "help":
        update.message.reply_text(
            text="*Here is 🗒️list of things i can do for you:*\n"
            "🔍*Extract subtitle from youtube links in different languages*\n"
            "🔠Translate subtitle of pariticular video in different languages\n\n"
            "*To extract subtitle follow this step:*\n"
            "👉_Click on Extract subtitle then give your link of youtube video from which you want to extract subtitle_\n"
            "👉_Click on available language or click on translate to translate subtitle into the unavaliable language_\n"
            "🔐_choose format 'VTT' or 'SRT'_\n"
            "🙃Done\n\n"
            "*To extract subtitle from Age ristricted youtube video follow this step:*\n"
            "🔴_Will implement this feature in future currently it will not work for age ristricted videos_",
            parse_mode=ParseMode.MARKDOWN_V2
        )


format_button = [[InlineKeyboardButton(text="SRT", callback_data="SRT")], [
    InlineKeyboardButton(text='VTT', callback_data="VTT")], [InlineKeyboardButton(text="🔙 Back", callback_data="back")]]

format_button_markup = InlineKeyboardMarkup(format_button)


def choosing_language(update: Update, context: CallbackContext):
    user_language = update.callback_query.data
    if user_language == ">>" or user_language == "<<":
        button_list = context.user_data["button_list"]
        page_no = context.user_data.get("page_no")
        if user_language == ">>":
            context.user_data["count"] += 1
            if context.user_data["count"] == page_no:
                context.user_data["count"] = 1
        if user_language == "<<":
            context.user_data["count"] -= 1
            if context.user_data["count"] < 1:
                context.user_data["count"] = page_no - 1
        count = context.user_data.get("count")
        update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(button_list[count]))
        return CHOOSING_LANGUAGE
    language_dictionary = context.user_data.get('language_dictionary')
    language = list(language_dictionary.keys())
    video_id = context.user_data.get("video_id")
    context.user_data["language"] = user_language
    selected_language = update.callback_query.message.edit_text(
        "🔠 *language selected*: {} ".format(escape_markdown(user_language, version=2)),
        parse_mode=ParseMode.MARKDOWN_V2)
    context.user_data["selected_language"] = selected_language
    if user_language in language:
        language_code = language_dictionary[user_language]
        returned_data = YouTubeTranscriptApi.get_transcript(
            video_id, languages=[language_code])
        context.user_data["returned_data"] = returned_data
    else:
        translate_dictionary = context.user_data["translate_dictionary"]
        language_code = translate_dictionary[user_language]
        transcript = context.user_data["transcript"]
        translated_transcript = transcript.translate(f'{language_code}')
        returned_data = translated_transcript.fetch()
        context.user_data["returned_data"] = returned_data

    update.callback_query.message.reply_text(
        text="🧖 *In which format do want your subtitle?:*",
        reply_markup=format_button_markup,
        parse_mode=ParseMode.MARKDOWN_V2)
    return CHOOSING_FORMAT


def translate(update: Update, context: CallbackContext):
    language_dictionary = context.user_data.get('language_dictionary')
    video_id = context.user_data.get("video_id")
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    try:
        transcript = transcript_list.find_transcript(["en"])
    except:
        transcript = transcript_list.find_transcript(
            [f'{list(language_dictionary.values())[0]}'])
        pass
    context.user_data["transcript"] = transcript
    translate_list = transcript.translation_languages
    button_list = []
    translate_dictionary = {}
    for i in range(0, len(translate_list), 2):
        language = translate_list[i]["language"]
        language_code = translate_list[i]["language_code"]
        translate_dictionary[language] = language_code
        try:
            language2 = translate_list[i+1]["language"]
            language_code2 = translate_list[i+1]["language_code"]
            translate_dictionary[language2] = language_code2
            translate_button = [InlineKeyboardButton(text=language, callback_data=language), InlineKeyboardButton(
                text=language2, callback_data=language2)]
        except IndexError:
            translate_button = [InlineKeyboardButton(
                text=language, callback_data=language)]
        button_list.append(translate_button)
    button_list, page_no = button_formater(button_list)
    button_list_markup = InlineKeyboardMarkup(button_list[1])
    context.user_data["translate_dictionary"] = translate_dictionary
    context.user_data["button_list"] = button_list
    context.user_data["page_no"] = page_no
    context.user_data["button_list_markup"] = button_list_markup
    context.user_data["count"] = 1
    update.callback_query.message.edit_text(
        text="⌨️ *Choose the language in which your want your subtitle to 🔄convert:*",
        reply_markup=button_list_markup,
        parse_mode=ParseMode.MARKDOWN_V2)
    return CHOOSING_LANGUAGE


def choosing_format(update: Update, context: CallbackContext):
    user_format = update.callback_query.data
    returned_data = context.user_data.get("returned_data")
    if user_format == "back":
        selected_language = context.user_data.get("selected_language")
        selected_language.delete()
        if context.user_data.get("button_list_markup"):
            button_list_markup = context.user_data["button_list_markup"]
            update.callback_query.message.edit_text(
                text="⌨️*Choose the language in which your want your subtitle to 🔄convert:*",
                reply_markup=button_list_markup,
                parse_mode=ParseMode.MARKDOWN_V2)
        else:
            language_button = context.user_data.get("language_button")
            update.callback_query.message.edit_text(text="*⏬Choose the available language in this video or Click on* _Translate_ *to translate subtitle to other 🉐languages:*",
                                                    reply_markup=language_button,
                                                    parse_mode=ParseMode.MARKDOWN_V2)
        return CHOOSING_LANGUAGE
    user_chat_id = update.callback_query.message.chat_id
    bot_message = update.callback_query.message.edit_text(
        text="🟢*Your subtitle is ready:*",
        parse_mode=ParseMode.MARKDOWN_V2)
    lines = []
    for i, line in enumerate(returned_data):
        if i < len(returned_data) - 1:
            time_text = "{} --> {}".format(
                make_timestamp(line["start"], user_format),
                make_timestamp(returned_data[i+1]['start'], user_format)
            )
        else:
            duration = line["start"] + line["duration"]
            time_text = "{} --> {}".format(
                make_timestamp(line["start"], user_format),
                make_timestamp(duration, user_format)
            )
        if user_format == "VTT":
            lines.append("{}\n{}".format(time_text, line['text']))
        if user_format == "SRT":
            lines.append(
                str(i+1)+'\n'+"{}\n{}".format(time_text, line['text']))
    if user_format == "VTT":
        formated_string = "WEBVTT\n\n" + "\n\n".join(lines) + "\n"
        create_file(formated_string, 'vtt', user_chat_id)
    if user_format == "SRT":
        formated_string = "\n\n".join(lines) + "\n"
        create_file(formated_string, 'srt', user_chat_id)
    video_id = context.user_data.get('video_id')
    my_file_name = video_title(video_id)
    context.bot.send_document(user_chat_id, open(
        f"{user_chat_id}.{user_format.lower()}", "rb"), f"{my_file_name}.{user_format.lower()}",
        reply_markup=choose_button_markup, caption=f"Made with 🧠 \n~by @{bot_message.from_user.username}")
    os.remove(f"{user_chat_id}.{user_format.lower()}")
    return CHOOSING


def sending_youtube_url(update: Update, context: CallbackContext):
    user_text = update.message.text
    video_id = is_url(user_text)
    context.user_data["video_id"] = video_id
    if video_id is None:
        update.message.reply_text(
            text="🚫*Your link doesn't seem to be any video link of youtube, please 🕵️‍♀️check the 🔗link and try again*",
            reply_markup=choose_button_markup,
            parse_mode=ParseMode.MARKDOWN_V2)
        return CHOOSING
    else:
        button_dictionary = no_of_subtitle(video_id, update)
        if button_dictionary == CHOOSING:
            return CHOOSING
        language_button, language_dictionary = button_dictionary
        update.message.reply_text(text="*⏬Choose the available language in this video or Click on* _Translate_ *to translate subtitle to other 🉐languages:*",
                                  reply_markup=language_button, parse_mode=ParseMode.MARKDOWN_V2)
        context.user_data["language_button"] = language_button
        context.user_data["language_dictionary"] = language_dictionary
        return CHOOSING_LANGUAGE


def done(update: Update, context: CallbackContext):
    update.message.reply_text(
        text="*Ok see you later, 🥱send me* /start *to wake me*",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.MARKDOWN_V2)
    return ConversationHandler.END


def main():
    persistence = PicklePersistence(filename="Youtube_link")
    try:
        updater = Updater(token=os.getenv("API_TOKEN"),
                          persistence=persistence)
        dispatcher = updater.dispatcher
    except Exception as e:
        log.exception(e)
        exit(1)

    conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
        ],
        states={
            CHOOSING: [
                MessageHandler(
                    Filters.regex(
                        '^(Extract subtitle|Help|👻 Extract subtitle|ℹ️ Help|extract subtitle|help)$',
                    ),
                    choosing
                )
            ],
            SENDING_YOUTUBE_URL: [
                MessageHandler(
                    Filters.text & ~(Filters.command |
                                     Filters.regex('^Done$')),
                    sending_youtube_url
                )
            ],
            CHOOSING_LANGUAGE: [
                CallbackQueryHandler(
                    choosing_language, pattern=r'[\w><:]+[^(Translate)]'),
                CallbackQueryHandler(translate, pattern='^Translate$')

            ],
            CHOOSING_FORMAT: [
                CallbackQueryHandler(
                    choosing_format, pattern=r'^(SRT|VTT|back)$')
            ],
        },
        fallbacks=[CommandHandler("start", start), MessageHandler(
            Filters.regex('^(👋Done|Done|done)$',), done)],
        name="conversation_with_user",
        persistent=True
    )

    dispatcher.add_handler(conversation_handler)
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
