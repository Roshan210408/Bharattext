"""Small, hand-picked stopword lists per script.

These are deliberately short: they remove the most common function words so
the frequency chart shows content words. Extend them for serious work.
Lists are keyed by script (see scripts.py), not by language.
"""

ENGLISH = set("""
a about above after again against all am an and any are as at be because been
before being below between both but by can could did do does doing down during
each few for from further had has have having he her here hers herself him
himself his how i if in into is it its itself just me more most my myself no
nor not now of off on once only or other our ours ourselves out over own same
she should so some such than that the their theirs them themselves then there
these they this those through to too under until up very was we were what when
where which while who whom why will with would you your yours yourself
yourselves also may might must shall s t don't it's i'm
""".split())

HINDI = set("""
है हैं था थी थे हो होता होती होते का की के को में से पर और या तो भी ही
ने कि जो यह वह ये वे इस उस इन उन एक कुछ कोई क्या लिए तक साथ बहुत अब जब
तब नहीं न कर करना करते किया गया गई गए जाता जाती जाते रहा रही रहे सकता
सकती सकते हम मैं आप तुम अपना अपनी अपने यहाँ वहाँ यहां वहां अगर लेकिन
किसी किस कौन जैसे ऐसे वाला वाली वाले द्वारा
""".split())

TAMIL = set("""
ஒரு மற்றும் இந்த அந்த என்று என ஆனால் அது இது அவர் அவள் அவன் நான் நாம்
நாங்கள் நீ நீங்கள் அவர்கள் உள்ள உள்ளது இருந்து இருக்கும் என்ற போன்ற
மிகவும் தான் கூட பல சில எந்த அல்லது மேலும் இல்லை ஆகும் வரை பற்றி மீது
போது அங்கு இங்கு எல்லா எல்லாம் ஏன் என்ன யார் எப்படி
""".split())

MALAYALAM = set("""
ഒരു ഈ ആ എന്ന് എന്ന അത് ഇത് അവൻ അവൾ അവർ ഞാൻ നാം നമ്മൾ ഞങ്ങൾ നീ
നിങ്ങൾ ആണ് ഉണ്ട് ഇല്ല പക്ഷേ എന്നാൽ അല്ലെങ്കിൽ കൂടാതെ വളരെ എല്ലാ ചില
പല ഏത് എന്ത് പോലെ വേണ്ടി കൊണ്ട് മുതൽ വരെ ശേഷം മാത്രം തന്നെ ആയി ആയ
അവിടെ ഇവിടെ എന്നിവ എന്തുകൊണ്ട്
""".split())

BY_SCRIPT = {
    "Latin": ENGLISH,
    "Devanagari": HINDI,
    "Tamil": TAMIL,
    "Malayalam": MALAYALAM,
}

ALL = set().union(*BY_SCRIPT.values())
