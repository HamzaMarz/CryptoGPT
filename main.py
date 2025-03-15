import google.generativeai as genai
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters
import re
import requests

# تحميل التوكن من ملف .env
TOKEN = "8086483181:AAF5tegHNgpmI6OEKaZmXCcssAO3YlIjP1E"
GEMINI_API_KEY = "AIzaSyBi4JfxNYmdXGw5zvozN1Dsgo9G8weRopo"
COINMARKETCAP_API_KEY = "5d56cff1-d588-47f7-8236-0c3fbc5c1bdc"  # استبدل هذا بمفتاح API الخاص بك

# إعداد Gemini API
genai.configure(api_key=GEMINI_API_KEY)
generation_config = {
    "temperature": 1.1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
model = genai.GenerativeModel(
    model_name="gemini-2.0-pro-exp-02-05",
    generation_config=generation_config,
)
chat_session = model.start_chat(history=[])

# لوحة المفاتيح الرئيسية
main_keyboard = ReplyKeyboardMarkup([["محادثة عامة", "تحليل الأخبار الإقتصادية", "الحكم الشرعي", "أسعار العملات"]], resize_keyboard=True)

# لوحة المفاتيح داخل الأقسام
section_keyboard = ReplyKeyboardMarkup([["إنهاء المحادثة"]], resize_keyboard=True)

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("مرحبًا! أنا بوت CryptoGPT، مساعدك في عالم العملات الرقمية. اختر القسم الذي تريد استخدامه:", reply_markup=main_keyboard)

async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("اختر القسم الذي تريد استخدامه:", reply_markup=main_keyboard)

async def handle_section(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    if text == "محادثة عامة":
        await update.message.reply_text("اطرح سؤالك حول العملات الرقمية:", reply_markup=section_keyboard)
        context.user_data["section"] = "ask"
    elif text == "تحليل الأخبار الإقتصادية":
        await update.message.reply_text("أدخل نص الخبر لتحليله:", reply_markup=section_keyboard)
        context.user_data["section"] = "analyze"
    elif text == "الحكم الشرعي":
        await update.message.reply_text("""
لمعرفة حكم العملات الرقمية، اذهب البوت التالي: 
@CryptoGulfHalal_Bot
طريقة استخدامه:
تكتب حكم ثم اسم العملة المختصر
مثلاً لمعرفة حكم البيتكوين نكتب:
حكم BTC
    """, reply_markup=section_keyboard)
        context.user_data["section"] = "isHalal"
    elif text == "أسعار العملات":
        await update.message.reply_text("أدخل رمز العملة (مثل BTC أو ETH):", reply_markup=section_keyboard)
        context.user_data["section"] = "prices"
    else:
        return # تجاهل الرسائل النصية التي لا تتطابق مع الأقسام

async def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    if text == "إنهاء المحادثة":
        await update.message.reply_text("تم إنهاء المحادثة. اختر القسم الذي تريد استخدامه:", reply_markup=main_keyboard)
        if "section" in context.user_data:
            del context.user_data["section"]
        return

    section = context.user_data.get("section")
    if section == "ask":
        question = text
        prompt = f"""
        أنت خبير في العملات الرقمية والتداول، وأنت تعمل كدعم فني في شركة مختصة بالتداول الآلي باستخدام الذكاء الإصطناعي، قدم إجابة دقيقة وواضحة عن السؤال التالي:

        {question}

        اجعل الإجابة مختصرة ومباشرة، مع تقديم معلومات موثوقة حول العملات الرقمية والتداول عند الحاجة.
            إجابتك ستكون داخل بوت تلجرام، لذلك حسّن التنسيق حتى يكون ملائم واستخدم الايموجيز
        """
        response = chat_session.send_message(prompt)
        filtered_text = re.sub(r'\*\*', '', response.text)
        await update.message.reply_text(filtered_text, reply_markup=section_keyboard)
    elif section == "analyze":
        news_text = text
        prompt = f"""
        قم بتحليل تأثير الخبر التالي على سوق العملات الرقمية. قم بتقييم تأثيره على مقياس من 1 إلى 10، حيث 1 تأثير ضعيف و10 تأثير قوي جدًا.

        {news_text}

        قدم تحليلًا احترافيًا لشرح التأثير المحتمل على السوق والعملات المشهورة مثل البيتكوين والإيثريوم.

        إجابتك ستكون داخل بوت تلجرام، لذلك حسّن التنسيق حتى يكون ملائم واستخدم الايموجيز
        """
        response = chat_session.send_message(prompt)
        filtered_text = re.sub(r'\*\*', '', response.text)
        await update.message.reply_text(f"تحليل الخبر: {filtered_text}", reply_markup=section_keyboard)
    elif section == "prices":
        coin_symbol = text.upper()
        url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol={coin_symbol}"
        headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY,
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            price = data['data'][coin_symbol]['quote']['USD']['price']
            formatted_price = "{:.3f}".format(price)
            await update.message.reply_text(f"سعر {coin_symbol} الحالي: ${formatted_price}", reply_markup=section_keyboard)
        except requests.exceptions.RequestException as e:
            await update.message.reply_text(f"حدث خطأ: {e}", reply_markup=section_keyboard)
        except (KeyError, TypeError) as e:
            await update.message.reply_text("لم يتم العثور على العملة أو حدث خطأ في البيانات.", reply_markup=section_keyboard)
    else:
        return # تجاهل الرسائل النصية عندما لا يكون هناك قسم محدد

def main():
    app = Application.builder().token(TOKEN).build()

    # إضافة الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex("^(محادثة عامة|تحليل الأخبار الإقتصادية|الحكم الشرعي|أسعار العملات)$"), handle_section))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # تشغيل البوت
    app.run_polling()

if __name__ == "__main__":
    main()
