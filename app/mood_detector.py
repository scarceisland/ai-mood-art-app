import random

EMOTIONS = ["happiness", "sadness", "anger", "disgust", "fear", "surprise"]

ADVICE_BANK = {
    "happiness": [
        "Write down 3 things making you smile today.",
        "Share the vibe—send a kind message to someone.",
        "Take a quick walk and enjoy it.",
        "Capture the moment—take a photo for your mood gallery.",
        "Savour a small treat slowly, on purpose.",
        "Give a genuine compliment to someone nearby.",
        "Play your feel-good song all the way through.",
        "Set a tiny ‘win’ goal for later and celebrate it."
    ],
    "surprise": [
        "Pause and breathe—name what surprised you.",
        "Explore one small next step from this surprise.",
        "Tell a friend the story.",
        "Rate the surprise 1-10 and respond accordingly.",
        "Write one question this surprise raises.",
        "Check facts: what do you know vs. what are you assuming?",
        "Turn it into curiosity—look up one thing about it.",
        "If it’s good news, mark it in your calendar to remember."
    ],
    "sadness": [
        "Take 5 deep breaths and drink water.",
        "Write one sentence about how you feel.",
        "Move gently for 3 minutes.",
        "Sit by a window or step outside for 2 minutes of daylight.",
        "Send yourself kindness: ‘It’s okay to feel this.’",
        "Do a 60-second tidy of the space around you.",
        "Put on a gentle song and stretch your shoulders.",
        "Message one person just to check in."
    ],
    "anger": [
        "Box-breathe (4-4-4-4) before you speak.",
        "Name the need behind the anger.",
        "Do 10 slow squats to cool off.",
        "Delay replies—type it, don’t send; revisit in 10 minutes.",
        "Label it: ‘I feel angry because… I need…’",
        "Change temperature: splash cool water on your face.",
        "Walk around the room once before deciding what to do.",
        "Choose a boundary you can state calmly in one sentence."
    ],
    "disgust": [
        "Step away from the trigger and reset.",
        "Rinse your senses with a favourite song.",
        "Set a boundary for next time.",
        "If safe, remove or clean the source for 2 minutes.",
        "Name it out loud: ‘This feels gross; it will pass.’",
        "Breathe through your nose for 6 slow cycles.",
        "Sip mint or ginger tea to reset your palate.",
        "Visualise a protective bubble; step back in with intent."
    ],
    "fear": [
        "Ground yourself: 5-4-3-2-1 senses.",
        "Pick the smallest safe next action.",
        "Text someone you trust.",
        "Name the fear in one sentence; write it down.",
        "Ask: ‘What’s the worst, best, and most likely outcome?’",
        "Anchor with your feet: press them firmly into the floor.",
        "Set a 2-minute timer and plan only the first step.",
        "Recall one time you handled something similar."
    ]
}


def advice_for(emotion: str) -> str:
    """Returns a random piece of advice for a given emotion."""
    return random.choice(ADVICE_BANK.get(emotion, []))
