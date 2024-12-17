# **🤖 Buddy Travel**

Welcome to **Buddy Travel**—your go-to travel companion on Telegram! This bot is designed to simplify your travel planning by helping you with **flight searches**, **travel checklists**, and **personalized recommendations**.

---

## **About Buddy Travel**

With **Buddy Travel**, you can:
- ✈️ **Search flights** using the Google Flight API.  
- ✅ **Manage travel checklists** to keep track of everything you need.  
- 🧠 **Get personalized travel recommendations** powered by AI.  


Try it now: [Buddy Travel on Telegram](https://t.me/buddy_travel_bot)

---

## **Features**

### **✈️ Flight Search** 
- Use the `/searchflight` command to find flights easily.  
- **User input example**: `Tel Aviv, Dubai, 11.08.2024, 15.08.2024`.  
- **Bot response**:  
   * Searching for flights from Tel Aviv to Dubai...  
   * Lists flights with details:  
     - **Airline**  
     - **Flight duration**  
     - **Layovers**  
     - **Carbon emission estimates**  
- Works with city names, country names, or airport names.

---

### **✅ Travel Checklist** 
Manage your packing and preparation with a simple checklist:
- 📋 **Show Checklist**: View all current checklist items.  
- 🆕 **Start New Checklist**: Clear and reset the checklist.  
- ➕ **Add Item**: Add new items to your travel checklist.  
- 🗑️ **Delete Item**: Remove unnecessary items.  
- 🔄 **Update Status**: Mark items as "done" or "not done".

Use `/start` to interact with the checklist options easily.

---

### **🧠 AI-Powered Recommendations** 
- Get personalized recommendations for your destination using the `/recommendation` command.
- Input a **city** or **country name**, and the bot will generate top attractions, travel tips, and more.

**Example**:  
**User input**: `Tel Aviv`  
**Bot response**:  
```
🏖️ Tel Aviv: A City That Never Sleeps  

Top Attractions:  
- The Beaches: Gordon Beach, Hilton Beach.  
- Bauhaus Architecture: Walking tours to explore unique buildings.  
- Carmel Market: Fresh produce and souvenirs.  
- Neve Tzedek Neighborhood: Charming cafes and art galleries.  

Travel Tips:  
- Food: Try hummus, falafel, and shawarma 🥙.  
- Nightlife: Explore vibrant clubs and bars.  
- Weather: Hot summers, mild winters ☀️🌧️.  
```

---

## **Languages 🌍**
Buddy Travel supports **four languages**:
- 🇬🇧 **English**  
- 🇮🇱 **Hebrew**  
- 🇸🇦 **Arabic**  
- 🇷🇺 **Russian**  

Additional translations can be added in the `translation.py` file.

---

## **How It Works**

### **Commands**
- `/searchflight` - Find flights (round trip or one-way).  
- `/start` - Manage your travel checklist.  
- `/recommendation` - Get AI-powered travel tips and attractions.  

### **Interaction**
The bot guides you step-by-step with clear options to:  
1. Search flights.  
2. Manage your checklist.  
3. Receive travel recommendations.  

---

## **Setup for Developers**

### **Prerequisites**
- 🐍 **Python 3.11**  
- 🧩 **Poetry** (for dependency management).  
- 🗂️ **MongoDB** (for storing user data).  

### **Setup Instructions**
1. Install dependencies:
   ```bash
   poetry install
   ```

2. Create a `config.py` file in the project root. Use this template:
   ```python
   TELEGRAM_TOKEN = 'Your Telegram Bot Token'
   MONGODB_URI = 'Your MongoDB URI'
   GEMINI_API_KEY = 'Your Gemini API Key'
   GOOGLE_FLIGHTS_API = 'Google Flights API Key'  # Example: SerpAPI
   ```

3. Start the bot:
   ```bash
   poetry run python bot.py
   ```

---

## **Future Improvements 🛠️**
- 📊 Add price comparison features for flights.  
- 🌐 Expand recommendations to include local events and restaurants.  
- 🔄 Integrate voice commands for interaction.

---

## **Contributing**

Contributions are welcome! To contribute:
1. Fork the repository.  
2. Create a new branch: `git checkout -b feature-branch`.  
3. Make your changes and test them.  
4. Submit a pull request.

---
# Buddy-Travel-Bot
