with open("d:/uzbekcodersbot/5millionsertifikat/run_visual_test.py", "r", encoding="utf-8") as f:
    text = f.read()

# 2.5x playback tezligini 3.6x ga oshirish
text = text.replace("2.5x tezlikda", "3.6x tezlikda")
text = text.replace("2.5X TABIIY", "3.6X TABIIY")
text = text.replace("2.5x da yakunlandi", "3.6x da yakunlandi")
text = text.replace("2.5x Zaxira", "3.6x Zaxira")
text = text.replace("v.playbackRate = 2.5;", "v.playbackRate = 3.6;")

with open("d:/uzbekcodersbot/5millionsertifikat/run_visual_test.py", "w", encoding="utf-8") as f:
    f.write(text)

print("SUCCESS: 3.6X tezlik o'rnatildi!")
