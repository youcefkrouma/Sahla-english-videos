# مهارات Claude لصناعة فيديوهات Sahla English

هذه المهارات مثبّتة في `.claude/skills/`، وClaude يحمّلها وحده في كل جلسة على هذا المشروع.
اطلب ما تريد بكلامك العادي، وهو يختار المهارة المناسبة.

| المهارة | المصدر | ماذا تفعل لك | مثال طلب |
|---|---|---|---|
| `ffmpeg-skill` | [kajisho5/ffmpeg-skill](https://github.com/kajisho5/ffmpeg-skill) (MIT) | المونتاج: قص، لصق، 9:16، ترجمة مكتوبة على الفيديو (يدعم العربية)، شعار، موسيقى تحت الصوت، توحيد الصوت، تصدير TikTok/Reels/Shorts وفحص الملف قبل النشر | "حط ترجمة عربية للفيديو 15 وصدّرو لتيك توك" |
| `remotion-best-practices` | [remotion-dev/skills](https://github.com/remotion-dev/skills) (رسمية) | فيديوهات متحركة بالكود: نصوص تظهر وتتحرك، كويز، عدّاد، كاريوكي للكلمات، قوالب ثابتة لكل حلقة | "دير قالب Remotion لكويز فيه 4 اختيارات" |
| `text-to-speech` | [elevenlabs/skills](https://github.com/elevenlabs/skills) (رسمية، MIT) | صوت فهيمو والتعليق الصوتي بالعربية والإنجليزية | "ولّد صوت فهيمو يقول: Good morning!" |
| `speech-to-text` | ElevenLabs (رسمية) | تفريغ الصوت إلى نص وملفات ترجمة SRT بتوقيت دقيق | "خرّج ملف SRT من صوت الفيديو 12" |
| `sound-effects` | ElevenLabs (رسمية) | مؤثرات صوتية: تصفيق، "دينغ" للإجابة الصحيحة، انتقالات | "دير صوت دينغ قصير للجواب الصح" |
| `music` | ElevenLabs (رسمية) | موسيقى خلفية وجنغل خاص بالقناة | "دير جنغل 5 ثواني فرحان للأطفال" |
| `character-design` | [fal-ai-community/skills](https://github.com/fal-ai-community/skills) (رسمية، MIT) | الحفاظ على شكل فهيمو نفسه في كل صورة (نظام "المرتكزات") | "صوّر فهيمو في المطبخ بنفس شكل refs/fahimo-ref.png" |
| `fal-video-generation` | fal.ai (رسمية) | تحريك صورة إلى فيديو قصير (Kling وSeedance وVeo...) | "حرّك صورة الغلاف 3 ثواني" |
| `gemini-api-dev` | [google-gemini/gemini-skills](https://github.com/google-gemini/gemini-skills) (رسمية، Apache-2.0) | صور Nano Banana وتعديل الصور، فيديو Veo، صوت Gemini | "عدّل الغلاف وزيد نجوم حول فهيمو" |

## حالة الخدمات (فحص 2026-11-26)

- **ElevenLabs:** المفتاح يعمل.
- **Gemini:** المفتاح المربوط مرفوض (`API key not valid`). جدّد المفتاح في إعدادات البيئة قبل توليد الصور بـ Gemini.
- **fal.ai:** الرصيد نفد (`Exhausted balance`). اشحن الحساب من fal.ai/dashboard/billing قبل توليد الصور أو الفيديو بـ fal.
- **FFmpeg:** النسخة 6.1 مثبتة مع libass وfribidi وharfbuzz، فالترجمة العربية تظهر بحروف متصلة واتجاه صحيح.

## ملاحظات

- Remotion مجاني للأفراد والشركات الصغيرة (حتى 3 أشخاص). التفاصيل في `remotion-best-practices/remotion-license`.
- لتحديث مهارة: انسخ مجلدها من جديد من المستودع الأصلي.
