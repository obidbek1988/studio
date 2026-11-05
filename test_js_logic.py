# Test time manipulation
js_code = """
(() => {
    const v = document.querySelector('video') || document.querySelector('#plyrID');
    if (!v) return 'No video';
    const dur = v.duration || 60;
    
    // Virtual time injection
    let step = 0;
    const interval = setInterval(() => {
        if (v.currentTime >= dur * 0.85 || step > 200) {
            clearInterval(interval);
            console.log("Virtual watch finished!");
            return;
        }
        v.currentTime = Math.min(dur, v.currentTime + 0.8);
        v.dispatchEvent(new Event('timeupdate'));
        step++;
    }, 50);
})()
"""
print("JS logic ready")
