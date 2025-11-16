const login = require("fca-unofficial");
const fs = require("fs");
const path = require("path");

// ✅ AppState load karein
let appState;
try {
    appState = JSON.parse(fs.readFileSync("appstate.json", "utf-8"));
    console.log("✅ AppState loaded successfully");
} catch (err) {
    console.error("❌ Error reading appstate.json:", err);
    process.exit(1);
}

// ✅ Data storage
const dataPath = path.join(__dirname, "targets.json");
const roastsPath = path.join(__dirname, "roasts.txt");

function readTargets() {
    try {
        return JSON.parse(fs.readFileSync(dataPath, "utf8"));
    } catch {
        return { uids: [], names: {} };
    }
}

function saveTargets(data) {
    fs.writeFileSync(dataPath, JSON.stringify(data, null, 2));
}

function loadRoasts() {
    try {
        const data = fs.readFileSync(roastsPath, "utf8");
        const roasts = data.split('\n')
            .filter(line => line.trim())
            .filter(line => !line.startsWith('//'));
        console.log(`✅ ${roasts.length} roasts loaded`);
        return roasts;
    } catch (err) {
        console.error("❌ Error loading roasts.txt:", err);
        return [
            "Default roast message 1",
            "Default roast message 2", 
            "Default roast message 3"
        ];
    }
}

// ✅ Configuration
const ownerUid = "100004730585694"; // YAHAN APNI UID DALDO
let targets = readTargets();
let enabled = targets.uids || [];
let names = targets.names || {};
let roasts = loadRoasts();

// ✅ Random roast generator
function getRandomRoast() {
    if (roasts.length === 0) {
        return "Kya roast karu? Tu already roasted hai!";
    }
    return roasts[Math.floor(Math.random() * roasts.length)];
}

// ✅ Admin commands handler
function handleAdminCommand(api, event, args) {
    if (event.senderID.toString() !== ownerUid) {
        api.sendMessage("❌ Only owner can use this command.", event.threadID);
        return;
    }

    if (args.length === 0) {
        api.sendMessage("🎯 Target Bot Commands:\n• target list - Show all targets\n• target <uid> on - Target user by UID\n• target <uid> off - Remove target\n• target reload - Reload roasts", event.threadID);
        return;
    }

    const action = args[0].toLowerCase();

    // Show target list
    if (action === "list") {
        if (enabled.length === 0) {
            api.sendMessage("📭 No active targets.", event.threadID);
        } else {
            let list = "🎯 Active Targets:\n\n";
            enabled.forEach((uid, index) => {
                list += `${index + 1}. ${names[uid] || "Unknown"} (${uid})\n`;
            });
            api.sendMessage(list, event.threadID);
        }
        return;
    }

    // Reload roasts
    if (action === "reload") {
        roasts = loadRoasts();
        api.sendMessage(`✅ Roasts reloaded! Total: ${roasts.length}`, event.threadID);
        return;
    }

    // Enable/disable targets by UID
    if (args.length < 2) {
        api.sendMessage("❌ Usage: target <UID> on/off", event.threadID);
        return;
    }

    const targetUid = args[0];
    const mode = args[1].toLowerCase();

    // Validate UID (should be numeric)
    if (!/^\d+$/.test(targetUid)) {
        api.sendMessage("❌ Invalid UID. UID should contain only numbers.", event.threadID);
        return;
    }

    if (mode === "on") {
        // Get user info for name
        api.getUserInfo(targetUid, (err, userInfo) => {
            let userName = "Unknown";
            if (!err && userInfo[targetUid]) {
                userName = userInfo[targetUid].name || "Unknown";
            }

            if (!enabled.includes(targetUid)) {
                enabled.push(targetUid);
            }
            names[targetUid] = userName;
            saveTargets({ uids: enabled, names });
            
            api.sendMessage(`😈 TARGET ADDED:\nName: ${userName}\nUID: ${targetUid}`, event.threadID);
            console.log(`✅ Target added: ${userName} (${targetUid})`);
        });
    } 
    else if (mode === "off") {
        const targetName = names[targetUid] || "Unknown";
        enabled = enabled.filter(uid => uid !== targetUid);
        delete names[targetUid];
        saveTargets({ uids: enabled, names });
        
        api.sendMessage(`👿 TARGET REMOVED:\nUID: ${targetUid}\nName: ${targetName}`, event.threadID);
        console.log(`✅ Target removed: ${targetName} (${targetUid})`);
    } 
    else {
        api.sendMessage("❌ Usage: target <UID> on/off", event.threadID);
    }
}

// ✅ Target message handler
function handleTargetMessage(api, event) {
    const senderId = event.senderID.toString();
    
    if (enabled.includes(senderId)) {
        const userName = names[senderId] || "Unknown";
        const roast = getRandomRoast();
        
        console.log(`🎯 Roasting ${userName} (${senderId}): ${roast}`);
        
        // 2 second delay ke saath reply
        setTimeout(() => {
            api.sendMessage(roast, event.threadID, (err) => {
                if (err) {
                    console.error("❌ Failed to send roast:", err);
                } else {
                    console.log(`✅ Roast sent to ${userName}`);
                }
            });
        }, 2000);
    }
}

// 🟢 Facebook Login
login({ appState }, (err, api) => {
    if (err) {
        console.error("❌ Login Failed:", err);
        process.exit(1);
    }

    console.log("✅ Bot logged in successfully!");
    console.log(`🎯 Active targets: ${enabled.length}`);
    console.log(`🔥 Loaded roasts: ${roasts.length}`);
    console.log("🤖 Bot is now listening for messages...");

    // Set bot options
    api.setOptions({
        listenEvents: true,
        selfListen: false,
        logLevel: "silent"
    });

    // Listen for messages
    api.listen((err, event) => {
        if (err) {
            console.error("❌ Listen error:", err);
            return;
        }

        try {
            if (event.type === "message" && event.body) {
                const message = event.body.trim();
                
                // Check for target command
                if (message.startsWith('target ')) {
                    const args = message.split(' ').slice(1);
                    handleAdminCommand(api, event, args);
                } 
                // Check if message is from target user
                else {
                    handleTargetMessage(api, event);
                }
            }
        } catch (error) {
            console.error("❌ Error processing message:", error);
        }
    });
});

// ✅ Auto-save on exit
process.on('SIGINT', () => {
    console.log('💾 Saving targets before exit...');
    saveTargets({ uids: enabled, names });
    process.exit(0);
});

process.on('uncaughtException', (error) => {
    console.error('❌ Uncaught Exception:', error);
});
