<template>
  <div class="p-8 w-full">
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-white">Настройки организации</h1>
      <p class="text-slate-400 text-sm mt-1">{{ currentTabLabel }}</p>
    </div>

    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-8 h-8 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
    </div>

    <div v-else>
      <!-- TAB: General & Telegram -->
      <div v-show="activeTab === 'general'" class="bg-slate-900 rounded-2xl border border-slate-800 p-6 space-y-5">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="form-label">Название ресторана</label>
            <input id="input-org-name" v-model="form.name" type="text" class="form-input" placeholder="Мой Ресторан" />
          </div>
          <div>
            <label class="form-label">Slug <span class="text-slate-600">(read-only)</span></label>
            <input :value="form.slug" type="text" class="form-input opacity-50 cursor-not-allowed" readonly />
          </div>
        </div>
        <div>
          <label class="form-label">Адрес</label>
          <textarea id="input-org-address" v-model="form.address" class="form-input min-h-[80px] resize-none" placeholder="ул. Абая, 1"></textarea>
        </div>
        <hr class="border-slate-800">
        <div>
          <label class="form-label">Telegram Bot Token</label>
          <div class="relative">
            <input id="input-bot-token" v-model="form.tg_bot_token"
              :type="showToken ? 'text' : 'password'" class="form-input pr-12"
              placeholder="1234567890:ABCdef..." />
            <button type="button" @click="showToken = !showToken"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
              {{ showToken ? '🙈' : '👁' }}
            </button>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="form-label">Username бота <span class="text-slate-600">(без @)</span></label>
            <input id="input-bot-username" v-model="form.tg_bot_username" type="text" class="form-input" placeholder="my_loyalty_bot" />
          </div>
          <div>
            <label class="form-label">Имя Mini App</label>
            <input id="input-tma-name" v-model="form.tma_name" type="text" class="form-input" placeholder="loyalty" />
          </div>
        </div>
        <div>
          <label class="form-label">Прямая ссылка на TMA</label>
          <input id="input-tma-direct-link" v-model="form.tma_direct_link" type="url" class="form-input" placeholder="https://t.me/my_loyalty_bot/loyalty" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="form-label">Ссылка на Instagram</label>
            <input id="input-instagram-link" v-model="form.instagram_link" type="url" class="form-input" placeholder="https://instagram.com/my_restaurant" />
          </div>
          <div>
            <label class="form-label">Ссылка на WhatsApp</label>
            <input id="input-whatsapp-link" v-model="form.whatsapp_link" type="url" class="form-input" placeholder="https://wa.me/77071234567" />
          </div>
        </div>

        <hr class="border-slate-800">
        <!-- Webhook Status Block -->
        <div class="bg-slate-800/50 rounded-xl p-5 border border-slate-700/50">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-white font-medium flex items-center gap-2">
              <span class="text-indigo-400">🔗</span> Статус Telegram Webhook
            </h3>
            <div class="flex gap-2">
              <button @click="registerWebhook" :disabled="registeringWebhook || !form.tg_bot_token"
                class="px-3 py-1.5 text-xs font-medium rounded-lg transition-all duration-200
                       flex items-center gap-2 disabled:opacity-50"
                :class="registeringWebhook ? 'bg-emerald-600/50 text-emerald-200' : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-md hover:shadow-emerald-500/20'">
                <span v-if="registeringWebhook" class="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                <span v-else>➕</span>
                Установить Webhook
              </button>
              <button @click="checkWebhookStatus" :disabled="checkingWebhook || !form.tg_bot_token"
                class="px-3 py-1.5 text-xs font-medium rounded-lg transition-all duration-200
                       flex items-center gap-2 disabled:opacity-50"
                :class="checkingWebhook ? 'bg-indigo-600/50 text-indigo-200' : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md hover:shadow-indigo-500/20'">
                <span v-if="checkingWebhook" class="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                <span v-else>🔄</span>
                Проверить статус
              </button>
              <button @click="openTestModal" :disabled="sendingTest || !form.tg_bot_token"
                class="px-3 py-1.5 text-xs font-medium bg-slate-700 hover:bg-slate-650 text-slate-200 rounded-lg transition-all duration-200
                       flex items-center gap-2 disabled:opacity-50 shadow-md">
                <span>🧪</span>
                Отправить тест
              </button>
            </div>
          </div>
          
          <div v-if="webhookStatus" class="space-y-3 text-sm">
            <div class="grid grid-cols-[140px_1fr] gap-2 items-center">
              <span class="text-slate-400">Ожидаемый URL:</span>
              <span class="text-slate-200 font-mono text-xs truncate" :title="webhookStatus.expected_url">{{ webhookStatus.expected_url }}</span>
            </div>
            
            <div class="grid grid-cols-[140px_1fr] gap-2 items-center">
              <span class="text-slate-400">Установлен в TG:</span>
              <span class="text-slate-200 font-mono text-xs truncate" :title="webhookStatus.telegram_response?.url">
                {{ webhookStatus.telegram_response?.url || 'Не установлен' }}
              </span>
            </div>
            
            <div class="grid grid-cols-[140px_1fr] gap-2 items-center">
              <span class="text-slate-400">Статус:</span>
              <div class="flex items-center gap-2">
                <span v-if="webhookStatus.telegram_response?.url" class="flex items-center gap-1 text-emerald-400">
                  <span class="w-2 h-2 rounded-full bg-emerald-500"></span> Установлен
                </span>
                <span v-else class="flex items-center gap-1 text-amber-400">
                  <span class="w-2 h-2 rounded-full bg-amber-500"></span> Отсутствует
                </span>
                
                <span v-if="webhookStatus.telegram_response?.pending_update_count > 0" class="px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-medium border border-indigo-500/30">
                  Очередь: {{ webhookStatus.telegram_response.pending_update_count }}
                </span>
              </div>
            </div>
            
            <div v-if="webhookStatus.telegram_response?.last_error_message" class="mt-3 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p class="text-red-400 text-xs font-medium mb-1">Последняя ошибка от Telegram:</p>
              <p class="text-red-300 text-xs font-mono break-words">{{ webhookStatus.telegram_response.last_error_message }}</p>
              <p v-if="webhookStatus.telegram_response.last_error_date" class="text-red-500/60 text-[10px] mt-1">
                Дата: {{ new Date(webhookStatus.telegram_response.last_error_date * 1000).toLocaleString() }}
              </p>
            </div>
          </div>
          
          <div v-else class="text-center py-4 text-slate-500 text-sm">
            Нажмите "Проверить статус", чтобы загрузить данные от Telegram
          </div>
        </div>

        <div class="flex justify-end pt-2">
          <SaveButton :saving="saving" @save="saveSettings" />
        </div>
      </div>

      <!-- TAB: WhatsApp WABA -->
      <div v-show="activeTab === 'waba'" class="space-y-6">
        <!-- Main settings box -->
        <div class="bg-slate-900 rounded-2xl border border-slate-800 p-6 space-y-6">
          <div class="flex items-center justify-between border-b border-slate-800 pb-5">
            <div>
              <div class="flex items-center gap-2">
                <span class="text-2xl">💬</span>
                <h2 class="text-lg font-bold text-white">Интеграция WhatsApp WABA</h2>
                <span class="px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  Cloud API
                </span>
              </div>
              <p class="text-slate-400 text-sm mt-1">Отправка сервисных сообщений и кодов авторизации через официальный WhatsApp Business API</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="form.is_waba_enabled" class="sr-only peer">
              <div class="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
              <span class="ml-3 text-sm font-medium" :class="form.is_waba_enabled ? 'text-emerald-400' : 'text-slate-500'">
                {{ form.is_waba_enabled ? 'Включено' : 'Выключено' }}
              </span>
            </label>
          </div>

          <!-- Webhook notification banner -->
          <div class="bg-slate-800/60 rounded-xl p-4 border border-slate-700/60 flex items-start justify-between gap-4">
            <div class="space-y-1">
              <div class="flex items-center gap-2">
                <span class="text-indigo-400 font-semibold text-sm">🔗 Вебхук iikoCard / iiko Cloud:</span>
                <span class="text-xs bg-indigo-500/10 text-indigo-300 px-2 py-0.5 rounded border border-indigo-500/20">Единый URL</span>
              </div>
              <p class="text-xs text-slate-400">
                Вставьте этот URL в настройках вебхуков в iikoCard / RMS. Все транзакции и коды подтверждения будут поступать сюда и автоматически отправляться в WhatsApp по настроенным правилам.
              </p>
              <div class="font-mono text-xs text-indigo-300 bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-700 w-fit select-all">
                {{ webhookUrl }}
              </div>
            </div>
            <button @click="copyWebhookUrl" class="px-3 py-1.5 text-xs font-medium bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg transition-all shrink-0">
              📋 Скопировать
            </button>
          </div>

          <!-- Credentials inputs -->
          <div class="space-y-4">
            <div>
              <label class="form-label">Meta Access Token (System User Permanent Token)</label>
              <div class="relative">
                <input v-model="form.waba_access_token" :type="showWabaToken ? 'text' : 'password'" class="form-input pr-12 font-mono text-xs" placeholder="EAAB..." />
                <button type="button" @click="showWabaToken = !showWabaToken"
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
                  {{ showWabaToken ? '🙈' : '👁' }}
                </button>
              </div>
              <p class="text-[11px] text-slate-500 mt-1">
                Токен системного пользователя Meta Business Manager с правами <code>whatsapp_business_messaging</code> и <code>whatsapp_business_management</code>.
              </p>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="form-label">WhatsApp Business Account ID (WABA ID)</label>
                <input v-model="form.waba_business_account_id" type="text" class="form-input font-mono text-sm" placeholder="например: 105938472910..." />
                <p class="text-[11px] text-slate-500 mt-1">ID аккаунта для выгрузки шаблонов и телефонных номеров.</p>
              </div>
              <div>
                <div class="flex items-center justify-between mb-1">
                  <label class="form-label !mb-0">Phone Number ID</label>
                  <button v-if="form.waba_access_token && form.waba_business_account_id"
                    type="button"
                    @click="fetchWabaPhoneNumbers" :disabled="loadingWabaNumbers"
                    class="text-xs text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1 font-semibold">
                    <span v-if="loadingWabaNumbers" class="w-3 h-3 border border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin"></span>
                    <span>{{ loadingWabaNumbers ? 'Загрузка...' : '⚡ Загрузить из Meta' }}</span>
                  </button>
                </div>
                <div v-if="wabaPhoneNumbers.length > 0" class="space-y-1">
                  <select v-model="form.waba_phone_number_id" class="form-input font-mono text-sm">
                    <option value="">-- Выберите телефонный номер --</option>
                    <option v-for="num in wabaPhoneNumbers" :key="num.id" :value="num.id">
                      {{ num.display_phone_number }} (ID: {{ num.id }}{{ num.verified_name ? ' - ' + num.verified_name : '' }})
                    </option>
                  </select>
                </div>
                <input v-else v-model="form.waba_phone_number_id" type="text" class="form-input font-mono text-sm" placeholder="например: 525197927353331" />
                <p v-if="form.waba_phone_number_id && form.waba_business_account_id && form.waba_phone_number_id === form.waba_business_account_id" class="text-[11px] text-amber-400 mt-1 flex items-center gap-1 font-semibold">
                  ⚠️ Внимание: Phone Number ID не должен совпадать с Business Account ID! Нажмите «⚡ Загрузить из Meta».
                </p>
                <p v-else-if="form.waba_phone_number_id && (form.waba_phone_number_id.startsWith('+') || form.waba_phone_number_id.length <= 12)" class="text-[11px] text-amber-400 mt-1 flex items-center gap-1 font-semibold">
                  ⚠️ Внимание: Здесь нужен не сам телефонный номер, а цифровой ID номера из Meta (например, 525197927353331). Нажмите «⚡ Загрузить из Meta».
                </p>
                <p v-else class="text-[11px] text-slate-500 mt-1">Идентификатор телефонного номера Meta (15-значный цифровой ID), с которого отправляются сообщения.</p>
              </div>
            </div>
          </div>

          <!-- Actions toolbar -->
          <div class="flex items-center justify-between pt-2 border-t border-slate-800">
            <div class="flex items-center gap-2">
              <button @click="fetchWabaTemplates" :disabled="loadingWabaTemplates || !form.waba_access_token || !form.waba_business_account_id"
                class="px-4 py-2 text-xs font-semibold rounded-xl transition-all duration-200 flex items-center gap-2 disabled:opacity-50"
                :class="loadingWabaTemplates ? 'bg-indigo-600/50 text-indigo-200' : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md hover:shadow-indigo-500/20'">
                <span v-if="loadingWabaTemplates" class="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                <span v-else>📥</span>
                Выгрузить шаблоны из Meta
              </button>

              <button @click="openWabaTestModal" :disabled="!form.waba_access_token || !form.waba_phone_number_id"
                class="px-4 py-2 text-xs font-semibold bg-slate-800 hover:bg-slate-750 text-slate-200 rounded-xl transition-all border border-slate-700 disabled:opacity-50 flex items-center gap-2 shadow-sm">
                <span>🧪</span>
                Тестовая отправка
              </button>
            </div>

            <SaveButton :saving="saving" @save="saveSettings" />
          </div>
        </div>

        <!-- Available templates section -->
        <div v-if="wabaTemplates.length > 0" class="bg-slate-900 rounded-2xl border border-slate-800 p-6 space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-white font-bold flex items-center gap-2">
                <span>📑</span> Доступные шаблоны из Meta
                <span class="text-xs font-normal text-slate-400">({{ wabaTemplates.length }} шт.)</span>
              </h3>
              <p class="text-slate-400 text-xs mt-0.5">Утвержденные шаблоны в WhatsApp Business Manager</p>
            </div>
            <input v-model="templateSearchQuery" type="text" class="form-input !w-64 !py-1.5 text-xs" placeholder="Поиск по названию шаблона..." />
          </div>

          <div class="grid grid-cols-2 gap-3 max-h-72 overflow-y-auto pr-1">
            <div v-for="tmpl in filteredTemplates" :key="tmpl.id || tmpl.name"
              class="bg-slate-800/40 border border-slate-700/50 rounded-xl p-3.5 hover:border-slate-600 transition-all flex flex-col justify-between">
              <div>
                <div class="flex items-center justify-between mb-1.5">
                  <span class="font-mono text-xs font-semibold text-white truncate max-w-[200px]" :title="tmpl.name">{{ tmpl.name }}</span>
                  <div class="flex items-center gap-1.5">
                    <span class="text-[10px] px-2 py-0.5 rounded-full font-mono font-medium"
                      :class="tmpl.status === 'APPROVED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'">
                      {{ tmpl.status }}
                    </span>
                    <span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-700 text-slate-300 uppercase">{{ tmpl.language }}</span>
                  </div>
                </div>
                <p class="text-xs text-slate-400 line-clamp-2">
                  {{ getTemplateBodyText(tmpl) || 'Шаблон без текста' }}
                </p>
              </div>
              <div class="mt-2 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-500">
                <span>{{ tmpl.category }}</span>
                <button @click="openCreateRuleModalWithTemplate(tmpl)" class="text-indigo-400 hover:text-indigo-300 font-medium">
                  + Создать правило
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Trigger rules section -->
        <div class="bg-slate-900 rounded-2xl border border-slate-800 p-6 space-y-5">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-white font-bold flex items-center gap-2">
                <span>⚡</span> Сценарии отправки сообщений (Правила)
              </h3>
              <p class="text-slate-400 text-xs mt-0.5">Настройка автоотправки при получении вебхука от iiko</p>
            </div>
            <button @click="openCreateRuleModal()" class="px-3.5 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl transition-all flex items-center gap-1.5 shadow-md hover:shadow-indigo-500/20">
              <span>➕</span> Добавить правило
            </button>
          </div>

          <!-- Quick preset cards -->
          <div class="grid grid-cols-3 gap-4">
            <!-- Auth Code Card -->
            <div class="bg-slate-800/50 border rounded-xl p-4 transition-all"
              :class="authCodeRule ? (authCodeRule.is_enabled ? 'border-emerald-500/30 bg-emerald-950/10' : 'border-slate-700') : 'border-slate-800'">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xl">🔐</span>
                <span class="text-[11px] font-semibold px-2 py-0.5 rounded-full"
                  :class="authCodeRule?.is_enabled ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-700 text-slate-400'">
                  {{ authCodeRule?.is_enabled ? 'Включено' : (authCodeRule ? 'Отключено' : 'Не настроено') }}
                </span>
              </div>
              <h4 class="text-white font-semibold text-sm">Код авторизации</h4>
              <p class="text-xs text-slate-400 mt-1 line-clamp-1">
                {{ authCodeRule ? `Шаблон: ${authCodeRule.template_name}` : 'Отправка OTP кода гостю' }}
              </p>
              <div class="mt-4 pt-3 border-t border-slate-750 flex items-center justify-between">
                <button v-if="authCodeRule" @click="toggleRule(authCodeRule)" class="text-xs" :class="authCodeRule.is_enabled ? 'text-amber-400 hover:text-amber-300' : 'text-emerald-400 hover:text-emerald-300'">
                  {{ authCodeRule.is_enabled ? 'Отключить' : 'Включить' }}
                </button>
                <button @click="authCodeRule ? openEditRuleModal(authCodeRule) : openCreateRuleModal('auth_code')"
                  class="text-xs font-semibold text-indigo-400 hover:text-indigo-300 ml-auto">
                  {{ authCodeRule ? '⚙ Настроить' : '+ Подключить' }}
                </button>
              </div>
            </div>

            <!-- Balance Change Card -->
            <div class="bg-slate-800/50 border rounded-xl p-4 transition-all"
              :class="balanceRule ? (balanceRule.is_enabled ? 'border-emerald-500/30 bg-emerald-950/10' : 'border-slate-700') : 'border-slate-800'">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xl">💳</span>
                <span class="text-[11px] font-semibold px-2 py-0.5 rounded-full"
                  :class="balanceRule?.is_enabled ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-700 text-slate-400'">
                  {{ balanceRule?.is_enabled ? 'Включено' : (balanceRule ? 'Отключено' : 'Не настроено') }}
                </span>
              </div>
              <h4 class="text-white font-semibold text-sm">Баланс кошелька</h4>
              <p class="text-xs text-slate-400 mt-1 line-clamp-1">
                {{ balanceRule ? `Шаблон: ${balanceRule.template_name}` : 'Пополнение и списание бонусов' }}
              </p>
              <div class="mt-4 pt-3 border-t border-slate-750 flex items-center justify-between">
                <button v-if="balanceRule" @click="toggleRule(balanceRule)" class="text-xs" :class="balanceRule.is_enabled ? 'text-amber-400 hover:text-amber-300' : 'text-emerald-400 hover:text-emerald-300'">
                  {{ balanceRule.is_enabled ? 'Отключить' : 'Включить' }}
                </button>
                <button @click="balanceRule ? openEditRuleModal(balanceRule) : openCreateRuleModal('balance')"
                  class="text-xs font-semibold text-indigo-400 hover:text-indigo-300 ml-auto">
                  {{ balanceRule ? '⚙ Настроить' : '+ Подключить' }}
                </button>
              </div>
            </div>

            <!-- SimplePush Card -->
            <div class="bg-slate-800/50 border rounded-xl p-4 transition-all"
              :class="pushRule ? (pushRule.is_enabled ? 'border-emerald-500/30 bg-emerald-950/10' : 'border-slate-700') : 'border-slate-800'">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xl">📢</span>
                <span class="text-[11px] font-semibold px-2 py-0.5 rounded-full"
                  :class="pushRule?.is_enabled ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-700 text-slate-400'">
                  {{ pushRule?.is_enabled ? 'Включено' : (pushRule ? 'Отключено' : 'Не настроено') }}
                </span>
              </div>
              <h4 class="text-white font-semibold text-sm">Информационный пуш</h4>
              <p class="text-xs text-slate-400 mt-1 line-clamp-1">
                {{ pushRule ? `Шаблон: ${pushRule.template_name}` : 'Общие пуш-сообщения из iiko' }}
              </p>
              <div class="mt-4 pt-3 border-t border-slate-750 flex items-center justify-between">
                <button v-if="pushRule" @click="toggleRule(pushRule)" class="text-xs" :class="pushRule.is_enabled ? 'text-amber-400 hover:text-amber-300' : 'text-emerald-400 hover:text-emerald-300'">
                  {{ pushRule.is_enabled ? 'Отключить' : 'Включить' }}
                </button>
                <button @click="pushRule ? openEditRuleModal(pushRule) : openCreateRuleModal('push')"
                  class="text-xs font-semibold text-indigo-400 hover:text-indigo-300 ml-auto">
                  {{ pushRule ? '⚙ Настроить' : '+ Подключить' }}
                </button>
              </div>
            </div>
          </div>

          <!-- Rules list table if any custom rules or configured rules exist -->
          <div v-if="wabaRules.length > 0" class="mt-4">
            <h4 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Все активные правила</h4>
            <div class="divide-y divide-slate-800 border border-slate-800 rounded-xl overflow-hidden bg-slate-850/30">
              <div v-for="rule in wabaRules" :key="rule.id" class="p-3.5 flex items-center justify-between hover:bg-slate-800/40 transition-colors">
                <div class="flex items-center gap-3">
                  <span class="w-2.5 h-2.5 rounded-full" :class="rule.is_enabled ? 'bg-emerald-500' : 'bg-slate-600'"></span>
                  <div>
                    <span class="text-sm font-semibold text-white">{{ rule.name }}</span>
                    <span class="ml-2 text-xs text-slate-400 font-mono">({{ rule.template_name }} | {{ rule.template_language }})</span>
                  </div>
                </div>
                <div class="flex items-center gap-3">
                  <button @click="toggleRule(rule)" class="text-xs font-medium" :class="rule.is_enabled ? 'text-amber-400 hover:text-amber-300' : 'text-emerald-400 hover:text-emerald-300'">
                    {{ rule.is_enabled ? 'Отключить' : 'Включить' }}
                  </button>
                  <button @click="openEditRuleModal(rule)" class="text-xs font-medium text-indigo-400 hover:text-indigo-300">
                    Редактировать
                  </button>
                  <button @click="deleteRule(rule)" class="text-xs font-medium text-rose-400 hover:text-rose-300">
                    Удалить
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Dispatch Logs overview & launcher -->
        <div class="bg-slate-900 rounded-2xl border border-slate-800 p-6 space-y-4">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div class="flex items-center gap-2.5">
                <h3 class="text-white font-bold flex items-center gap-2">
                  <span>📜</span> Логи отправки сообщений WABA
                </h3>
                <span v-if="wabaLogsTotalCount > 0" class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  {{ wabaLogsTotalCount }} событий
                </span>
              </div>
              <p class="text-slate-400 text-xs mt-1">
                Журнал последних 100 отправок, фильтрация по периоду и выгрузка отчётов в Excel
              </p>
            </div>
            <div class="flex items-center gap-2">
              <button @click="openWabaLogsModal" class="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold transition-all shadow-md hover:shadow-indigo-500/20 flex items-center gap-2 cursor-pointer">
                <span>📋</span>
                <span>Открыть журнал логов (100 событий)</span>
              </button>
            </div>
          </div>

          <!-- Compact preview of recent logs -->
          <div v-if="wabaLogs.length > 0" class="pt-3 border-t border-slate-800/80">
            <div class="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span class="font-medium text-slate-400">Последние отправки:</span>
              <button @click="openWabaLogsModal" class="text-indigo-400 hover:text-indigo-300 font-medium">Смотреть все →</button>
            </div>
            <div class="space-y-1.5">
              <div v-for="log in wabaLogs.slice(0, 3)" :key="log.id" class="flex items-center justify-between py-2 px-3 rounded-xl bg-slate-950/70 border border-slate-800/60 text-xs">
                <div class="flex items-center gap-3">
                  <span class="font-mono text-slate-400 text-[11px]">{{ formatLogDate(log.created_at) }}</span>
                  <span class="font-mono font-medium text-white">{{ log.phone }}</span>
                  <span class="text-slate-400 text-[11px] hidden sm:inline">({{ log.template_name }})</span>
                </div>
                <div class="flex items-center gap-2">
                  <span v-if="log.status === 'SENT'" class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    ✓ Отправлено
                  </span>
                  <span v-else-if="log.status === 'FAILED'" class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                    ✕ Ошибка
                  </span>
                  <span v-else class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                    В очереди
                  </span>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="py-3 text-center text-slate-500 text-xs">
            Логи отправки сообщений пока отсутствуют
          </div>
        </div>
      </div>

      <!-- TAB: iiko Cloud API Integration -->
      <div v-show="activeTab === 'iiko'" class="bg-slate-900 rounded-2xl border border-slate-800 p-6 space-y-5">
        <div>
          <label class="form-label">Тип интеграции iiko</label>
          <select id="input-iiko-integration-type" v-model="form.iiko_integration_type" class="form-input">
            <option value="iiko_transport">iiko Cloud API (Transport)</option>
            <option value="iiko_card">iikoCard (Legacy)</option>
          </select>
        </div>
        <div>
          <label class="form-label">iiko API Base URL</label>
          <input id="input-iiko-url" v-model="form.iiko_api_base_url" type="url" class="form-input" placeholder="https://api-ru.iiko.services/api/1" />
        </div>
        <div>
          <label class="form-label">iiko API Login (apiKey)</label>
          <input id="input-iiko-login" v-model="form.iiko_api_login" type="password" class="form-input" placeholder="••••••••••" />
        </div>
        <div>
          <label class="form-label">iiko App ID (appId)</label>
          <input id="input-iiko-app-id" v-model="form.iiko_app_id" type="password" class="form-input" placeholder="••••••••••" />
        </div>
        <div>
          <label class="form-label">iiko Client Secret (clientSecret)</label>
          <input id="input-iiko-client-secret" v-model="form.iiko_client_secret" type="password" class="form-input" placeholder="••••••••••" />
        </div>
        <div>
          <label class="form-label">iiko Organization ID (uocId)</label>
          <input id="input-iiko-org-id" v-model="form.iiko_organization_id" type="text" class="form-input font-mono text-sm"
            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            pattern="[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
            title="UUID формат" />
          <p class="text-[11px] text-slate-400 mt-1">Для вебхуков iikoCard укажите <b>uocId</b> сети из вебхука.</p>
        </div>
        <div>
          <label class="form-label">iiko Loyalty Program ID</label>
          <input id="input-iiko-loyalty-id" v-model="form.iiko_loyalty_program_id" type="text" class="form-input font-mono text-sm"
            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            pattern="[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
            title="UUID формат" />
        </div>
        
        <hr class="border-slate-800">
        <div>
          <h3 class="text-white font-medium mb-3">Настройки Webhook</h3>
          
          <div class="mb-4 bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
            <label class="form-label">Ссылка для iiko Cloud (Webhook URL)</label>
            <div class="flex gap-2">
              <input type="text" readonly :value="webhookUrl" class="form-input font-mono text-sm opacity-70 bg-black/20 text-indigo-200" />
              <button @click="copyWebhookUrl" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors">
                Копировать
              </button>
            </div>
          </div>

          <div class="flex items-center gap-3 mb-4">
            <input type="checkbox" id="check-webhook-pass" v-model="form.is_iiko_webhook_password_enabled" class="w-5 h-5 rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-indigo-600 focus:ring-offset-slate-900" />
            <label for="check-webhook-pass" class="text-sm font-medium text-slate-300 select-none cursor-pointer">Включить проверку пароля для Webhook</label>
          </div>
          
          <div v-if="form.is_iiko_webhook_password_enabled" class="pl-8">
            <label class="form-label">Пароль вебхука (subscriptionPassword)</label>
            <input v-model="form.iiko_webhook_password" type="text" class="form-input" placeholder="Введите пароль..." />
          </div>
        </div>

        <div class="flex justify-between items-center pt-2 border-t border-slate-800">
          <button 
            type="button"
            @click="testIikoConnection" 
            :disabled="testingIiko" 
            class="px-4 py-2.5 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 rounded-xl text-sm font-medium transition-colors flex items-center gap-2 disabled:opacity-50 cursor-pointer"
          >
            <svg v-if="testingIiko" class="animate-spin -ml-1 mr-2 h-4 w-4 text-emerald-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>{{ testingIiko ? 'Проверка...' : 'Проверить подключение Cloud API' }}</span>
          </button>
          <SaveButton :saving="saving" @save="saveSettings" />
        </div>
      </div>

      <!-- TAB: iiko Server API Integration -->
      <div v-show="activeTab === 'iiko_server'" class="bg-slate-900 rounded-2xl border border-slate-800 p-6 space-y-5">
        <div>
          <h3 class="text-white font-medium mb-3 flex items-center gap-2">
            <span>🖥️</span> Настройки iiko Server (RMS / Chain)
          </h3>
          <p class="text-xs text-slate-400 mb-4">Настройки для подключения к вашему выделенному серверу iiko RMS или iiko Chain для работы с OLAP-отчетами и документами (накладными).</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="form-label">Адрес сервера (iiko Server URL)</label>
              <input id="input-iiko-server-url" v-model="form.iiko_server_url" type="url" class="form-input" placeholder="Например: https://banya-dastur.iiko.it:443" />
            </div>
            <div>
              <label class="form-label">Логин пользователя</label>
              <input id="input-iiko-server-login" v-model="form.iiko_server_login" type="text" class="form-input" placeholder="Введите логин..." />
            </div>
            <div class="md:col-span-2">
              <label class="form-label">Пароль пользователя</label>
              <input id="input-iiko-server-password" v-model="form.iiko_server_password" type="password" class="form-input" placeholder="••••••••••" />
            </div>
          </div>
        </div>

        <!-- Настройки OLAP-отчетов iiko -->
        <div v-if="form.is_analytics_enabled" class="bg-slate-800/50 rounded-xl p-5 border border-slate-700/50 mt-6 space-y-4">
          <div class="flex items-center justify-between border-b border-slate-700 pb-3">
            <h3 class="text-white font-medium flex items-center gap-2">
              <span class="text-indigo-400">📊</span> Настройки OLAP-отчетов iiko (RMS)
            </h3>
            <button type="button" @click="openCreatePresetModal"
              class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-3 py-1.5 rounded-lg font-semibold transition-all">
              + Добавить кастомный отчет
            </button>
          </div>

          <p class="text-xs text-slate-400">Укажите UUID (presetId) сохраненных отчетов из вашего RMS для автоматической синхронизации и AI-анализа.</p>

          <!-- List of Presets -->
          <div class="space-y-4 pt-2">
            <!-- System Presets -->
            <div v-for="preset in presets.filter(p => p.is_system)" :key="preset.id" 
              class="p-4 bg-slate-900/60 border border-slate-850 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div class="flex-1">
                <span class="text-xs text-indigo-400 font-semibold uppercase tracking-wider">Системный отчет</span>
                <h4 class="text-sm font-bold text-white mt-0.5">{{ preset.name }}</h4>
                <p class="text-xs text-slate-500 mt-1 max-w-lg leading-relaxed">{{ preset.description }}</p>
              </div>
              <div class="flex items-center gap-2 w-full md:w-auto">
                <input v-model="preset.preset_id" type="text" 
                  class="form-input font-mono text-xs w-full md:w-[280px]" 
                  placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
                <button type="button" @click="saveSystemPreset(preset)"
                  class="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs px-3 py-2 rounded-lg transition-all font-semibold">
                  Сохранить
                </button>
              </div>
            </div>

            <!-- Custom Presets -->
            <div v-for="preset in presets.filter(p => !p.is_system)" :key="preset.id"
              class="p-4 bg-slate-950/40 border border-slate-850 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-slate-800 transition-colors">
              <div class="flex-1">
                <span class="text-xs text-amber-400 font-semibold uppercase tracking-wider">Кастомный отчет (Только AI-анализ)</span>
                <h4 class="text-sm font-bold text-white mt-0.5">{{ preset.name }}</h4>
                <p class="text-xs text-slate-500 mt-1 max-w-lg leading-relaxed">{{ preset.description || 'Без описания.' }}</p>
                <div class="text-[11px] font-mono text-slate-500 mt-2">ID: {{ preset.preset_id }}</div>
              </div>
              <div class="flex items-center gap-3">
                <button type="button" @click="openEditPresetModal(preset)" class="text-xs text-indigo-400 hover:text-indigo-300 font-semibold">Редактировать</button>
                <button type="button" @click="deletePreset(preset)" class="text-xs text-rose-400 hover:text-rose-300 font-semibold">Удалить</button>
              </div>
            </div>

            <div v-if="!presets.length" class="text-center py-6 text-slate-500 text-xs">
              Загрузка пресетов отчетов...
            </div>
          </div>
        </div>

        <div class="flex justify-between items-center pt-2 border-t border-slate-800">
          <button 
            type="button"
            @click="testIikoServerConnection" 
            :disabled="testingIikoServer" 
            class="px-4 py-2.5 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 rounded-xl text-sm font-medium transition-colors flex items-center gap-2 disabled:opacity-50 cursor-pointer"
          >
            <svg v-if="testingIikoServer" class="animate-spin -ml-1 mr-2 h-4 w-4 text-indigo-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>{{ testingIikoServer ? 'Проверка...' : 'Проверить подключение Server API' }}</span>
          </button>
          <SaveButton :saving="saving" @save="saveSettings" />
        </div>
      </div>

      <!-- TAB: Card Tiers & Design (Single Source of Truth) -->
      <div v-show="activeTab === 'card_tiers'" class="bg-slate-900 rounded-2xl border border-slate-800 p-6 space-y-8">
        <!-- Header -->
        <div class="flex items-center justify-between pb-5 border-b border-slate-800">
          <div>
            <div class="flex items-center gap-2">
              <span class="text-2xl">💳</span>
              <h2 class="text-lg font-bold text-white">Ранги и дизайн карт лояльности</h2>
              <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Единый источник стиля
              </span>
            </div>
            <p class="text-slate-400 text-xs mt-1">
              Централизованное управление цветом бренда и автоматической сменой дизайна карт для всех каналов (TMA, Веб-онбординг, Google Wallet, Apple Wallet)
            </p>
          </div>
        </div>

        <!-- SECTION 1: Unified Base Brand & Card Color (BEFORE the toggle) -->
        <div class="bg-slate-950/70 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div class="flex items-start justify-between gap-4">
            <div>
              <h3 class="text-white text-sm font-bold flex items-center gap-2">
                <span>🎨</span> Базовый цвет бренда и карт лояльности
              </h3>
              <p class="text-slate-400 text-xs mt-1 leading-relaxed max-w-xl">
                Этот цвет является единым по умолчанию во всех точках касания с гостем. Если классификация ниже выключена (или гость не имеет специального ранга), все его карты автоматически окрашиваются в этот цвет.
              </p>
            </div>
          </div>

          <!-- Color controls -->
          <div class="flex flex-wrap items-center gap-4 pt-2">
            <div class="relative">
              <input
                id="input-unified-brand-color"
                type="color"
                v-model="brandColor"
                class="w-12 h-12 rounded-xl border-2 border-slate-700 cursor-pointer bg-transparent p-0.5"
              />
            </div>
            <input
              type="text"
              v-model="brandColor"
              class="form-input w-36 font-mono text-sm uppercase"
              placeholder="#6366F1"
            />
            <div
              class="w-12 h-12 rounded-xl border border-white/20 shadow-lg flex items-center justify-center text-xs font-bold text-white transition-all"
              :style="{ backgroundColor: brandColor }"
            >
              ✓
            </div>

            <!-- Quick palette chips -->
            <div class="flex items-center gap-1.5 flex-wrap">
              <span class="text-xs text-slate-500 mr-1">Быстрый выбор:</span>
              <button
                v-for="c in quickPalette"
                :key="c"
                type="button"
                @click="brandColor = c"
                class="w-6 h-6 rounded-lg border border-white/20 transition-transform hover:scale-110 active:scale-95 cursor-pointer shadow-sm"
                :style="{ backgroundColor: c }"
                :title="c"
              ></button>
            </div>
          </div>

          <!-- Touchpoints coverage badge list -->
          <div class="pt-3 border-t border-slate-800/80 flex flex-wrap items-center gap-2 text-[11px] text-slate-400">
            <span class="font-medium text-slate-300">Применяется в:</span>
            <span class="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-emerald-400 flex items-center gap-1 font-medium">
              ✓ Веб-онбординг
            </span>
            <span class="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-emerald-400 flex items-center gap-1 font-medium">
              ✓ Telegram Mini App
            </span>
            <span class="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-emerald-400 flex items-center gap-1 font-medium">
              ✓ Google Wallet
            </span>
            <span class="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-emerald-400 flex items-center gap-1 font-medium">
              ✓ Apple Wallet
            </span>
          </div>
        </div>

        <!-- SECTION 2: Classification Toggle -->
        <div class="bg-slate-950/70 border border-slate-800 rounded-2xl p-5 flex items-center justify-between">
          <div>
            <div class="flex items-center gap-2">
              <span class="text-lg">⭐</span>
              <h3 class="text-sm font-bold text-white">Классификация клиентов и ранги карт</h3>
            </div>
            <p class="text-xs text-slate-400 mt-1 max-w-xl">
              Включите, чтобы карты гостей динамически меняли цвет, металлический стиль и статус (Silver, Gold, VIP) на основе программ или категорий iiko.
            </p>
          </div>

          <label class="relative inline-flex items-center cursor-pointer flex-shrink-0">
            <input type="checkbox" v-model="form.is_client_classification_enabled" class="sr-only peer">
            <div class="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
            <span class="ml-3 text-sm font-medium" :class="form.is_client_classification_enabled ? 'text-emerald-400' : 'text-slate-500'">
              {{ form.is_client_classification_enabled ? 'Включено' : 'Выключено' }}
            </span>
          </label>
        </div>

        <!-- SECTION 3: Tiers Builder & Live Preview (Visible when classification is ON) -->
        <div v-if="form.is_client_classification_enabled" class="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
          <!-- Left Column: Tiers Constructor (7 cols) -->
          <div class="xl:col-span-7 space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <h4 class="text-sm font-bold text-white">Список уровней (рангов)</h4>
                <p class="text-xs text-slate-400">Настройте условия привязки и дизайн для каждого статуса</p>
              </div>
              <button
                type="button"
                @click="addTier"
                class="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-md flex items-center gap-1.5 transition-all cursor-pointer"
              >
                <span>➕</span> Добавить ранг
              </button>
            </div>

            <!-- Empty state -->
            <div v-if="!form.client_classification_settings?.tiers?.length" class="p-8 text-center bg-slate-950/40 border border-dashed border-slate-800 rounded-2xl space-y-3">
              <span class="text-3xl block">🏷️</span>
              <p class="text-xs text-slate-400">
                Уровни лояльности пока не добавлены. Нажмите «Добавить ранг», чтобы настроить Silver, Gold или VIP статус.
              </p>
              <button
                type="button"
                @click="addDefaultTiers"
                class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-medium transition-all cursor-pointer"
              >
                ✨ Добавить стандартные пресеты (Silver, Gold, VIP)
              </button>
            </div>

            <!-- Tiers List -->
            <div v-else class="space-y-4">
              <div
                v-for="(tier, idx) in form.client_classification_settings.tiers"
                :key="tier.id || idx"
                class="bg-slate-950/90 border border-slate-800 rounded-2xl p-4.5 space-y-4 transition-all"
                :class="{ 'ring-2 ring-indigo-500/50': previewTierId === tier.id }"
              >
                <!-- Tier Header -->
                <div class="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div class="flex items-center gap-2.5">
                    <div
                      class="w-6 h-6 rounded-lg border border-white/20 shadow-sm flex items-center justify-center text-xs font-bold text-white"
                      :style="{ backgroundColor: tier.color }"
                    >
                      {{ idx + 1 }}
                    </div>
                    <span class="text-sm font-bold text-white">{{ tier.name || 'Без названия' }}</span>
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-mono uppercase bg-black/40 border border-white/10 text-white/90">
                      {{ tier.badge || 'Pass' }}
                    </span>
                  </div>

                  <div class="flex items-center gap-2">
                    <button
                      type="button"
                      @click="previewTierId = tier.id"
                      class="px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer"
                      :class="previewTierId === tier.id ? 'bg-indigo-600 text-white' : 'bg-slate-800 hover:bg-slate-700 text-slate-300'"
                    >
                      👁️ Превью
                    </button>
                    <button
                      type="button"
                      @click="removeTier(idx)"
                      class="p-1 text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 rounded-lg transition-colors cursor-pointer"
                      title="Удалить ранг"
                    >
                      🗑️
                    </button>
                  </div>
                </div>

                <!-- Fields Grid -->
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                  <div>
                    <label class="form-label text-xs">Название ранга (RU)</label>
                    <input v-model="tier.name" type="text" class="form-input text-xs" placeholder="Например: Gold VIP" />
                  </div>
                  <div>
                    <label class="form-label text-xs">Название ранга (KZ)</label>
                    <input v-model="tier.name_kz" type="text" class="form-input text-xs" placeholder="Мысалы: Gold VIP" />
                  </div>

                  <div>
                    <label class="form-label text-xs">Текст бейджа на карте</label>
                    <input v-model="tier.badge" type="text" class="form-input text-xs font-mono" placeholder="Gold VIP Pass" />
                  </div>
                  <div>
                    <label class="form-label text-xs">Кэшбэк % (для отображения)</label>
                    <input v-model.number="tier.cashback_percent" type="number" class="form-input text-xs font-mono" placeholder="15" />
                  </div>
                </div>

                <!-- iiko matching criteria -->
                <div class="p-3 bg-slate-900/80 border border-slate-800/80 rounded-xl space-y-2.5">
                  <span class="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                    <span>🔗</span> Правило сопоставления с iiko
                  </span>

                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label class="block text-[11px] text-slate-400 mb-1">Программа лояльности из iiko</label>
                      <select v-model="tier.iiko_wallet_name" class="form-input text-xs">
                        <option value="">-- Выберите программу iiko --</option>
                        <option v-for="w in availableIikoWallets" :key="w" :value="w">{{ w }}</option>
                      </select>
                      <p class="text-[10px] text-slate-500 mt-0.5">Точное совпадение по названию кошелька</p>
                    </div>

                    <div>
                      <label class="block text-[11px] text-slate-400 mb-1">Или ключевые слова (через запятую)</label>
                      <input
                        v-model="tier.keywords"
                        type="text"
                        class="form-input text-xs font-mono"
                        placeholder="gold, золот, 15%"
                      />
                      <p class="text-[10px] text-slate-500 mt-0.5">Поиск в названии кошелька или категории гостя</p>
                    </div>
                  </div>
                </div>

                <!-- Style & Preset selector -->
                <div class="space-y-2">
                  <label class="form-label text-xs">Стиль и цвет карты</label>
                  <div class="flex flex-wrap items-center gap-2">
                    <button
                      v-for="preset in tierColorPresets"
                      :key="preset.id"
                      type="button"
                      @click="applyPresetToTier(tier, preset)"
                      class="px-2.5 py-1.5 rounded-xl text-xs font-medium border flex items-center gap-1.5 transition-all cursor-pointer"
                      :class="tier.gradient_preset === preset.id ? 'border-white text-white shadow-md' : 'border-slate-800 text-slate-400 hover:text-slate-200'"
                      :style="{ background: preset.gradient }"
                    >
                      <span class="w-2.5 h-2.5 rounded-full bg-white/40"></span>
                      <span class="text-white text-[11px] font-semibold">{{ preset.name }}</span>
                    </button>
                  </div>

                  <!-- Custom color override -->
                  <div class="flex items-center gap-3 pt-1">
                    <span class="text-xs text-slate-500">Пользовательский цвет:</span>
                    <input
                      type="color"
                      v-model="tier.color"
                      class="w-7 h-7 rounded-lg border border-slate-700 cursor-pointer bg-transparent p-0.5"
                    />
                    <input
                      type="text"
                      v-model="tier.color"
                      class="form-input w-28 font-mono text-xs uppercase"
                    />
                  </div>
                </div>

                <!-- Tier Banner (Apple Wallet strip & Google Wallet hero image) -->
                <div class="pt-3 border-t border-slate-800/80 space-y-2.5">
                  <div class="flex items-center justify-between">
                    <label class="form-label text-xs flex items-center gap-1.5 mb-0 font-semibold text-white">
                      <span>🖼️</span> Баннер карты для ранга (Apple Wallet & Google Wallet)
                    </label>
                    <span v-if="tier.banner_url" class="text-[10px] text-emerald-400 font-medium">✓ Баннер загружен</span>
                  </div>

                  <!-- Banner preview if uploaded -->
                  <div v-if="tier.banner_url" class="space-y-2">
                    <div class="relative w-full aspect-[2.6/1] max-h-28 rounded-xl overflow-hidden border border-slate-700 shadow-md bg-slate-900 group">
                      <img :src="tier.banner_url" alt="Banner" class="w-full h-full object-cover" />
                      <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                        <label class="px-3 py-1.5 bg-slate-900/90 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg border border-slate-600 cursor-pointer transition-all shadow">
                          <span>Заменить</span>
                          <input type="file" accept="image/png,image/jpeg,image/webp" class="hidden" @change="uploadTierBanner(tier, $event)" />
                        </label>
                        <button
                          type="button"
                          @click="tier.banner_url = ''"
                          class="px-3 py-1.5 bg-rose-950/90 hover:bg-rose-900 text-rose-300 text-xs font-semibold rounded-lg border border-rose-800 cursor-pointer transition-all shadow"
                        >
                          Удалить
                        </button>
                      </div>
                    </div>
                  </div>

                  <!-- Upload button if no banner -->
                  <div v-else class="flex flex-col sm:flex-row items-start sm:items-center gap-3">
                    <label class="cursor-pointer bg-slate-900 hover:bg-slate-850 border border-slate-700/80 hover:border-slate-600 text-slate-200 px-3.5 py-2 rounded-xl text-xs font-medium transition-all inline-flex items-center gap-2 shadow-sm">
                      <span v-if="uploadingTierBannerId === tier.id" class="w-3.5 h-3.5 border-2 border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin"></span>
                      <span>{{ uploadingTierBannerId === tier.id ? 'Загрузка...' : '📁 Загрузить баннер' }}</span>
                      <input
                        type="file"
                        accept="image/png,image/jpeg,image/webp"
                        class="hidden"
                        @change="uploadTierBanner(tier, $event)"
                        :disabled="uploadingTierBannerId === tier.id"
                      />
                    </label>
                    <p class="text-[11px] text-slate-400 leading-tight">
                      Рекомендуемый размер: <strong class="text-slate-300">1125 × 432 px</strong>. Отображается на картах Apple Wallet (strip) и Google Wallet.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Right Column: Interactive 3D Card Live Preview (5 cols) -->
          <div class="xl:col-span-5 sticky top-6 space-y-4">
            <div class="bg-slate-950/90 border border-slate-800 rounded-2xl p-5 space-y-4">
              <div class="flex items-center justify-between">
                <div>
                  <h4 class="text-sm font-bold text-white flex items-center gap-2">
                    <span>✨</span> Интерактивный предпросмотр
                  </h4>
                  <p class="text-xs text-slate-400">Нажмите на карту для 3D-переворота к QR-коду</p>
                </div>

                <!-- Preview target selector -->
                <select
                  v-model="previewTierId"
                  class="bg-slate-900 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none"
                >
                  <option value="base">Базовый цвет</option>
                  <option
                    v-for="t in form.client_classification_settings?.tiers || []"
                    :key="t.id"
                    :value="t.id"
                  >
                    {{ t.name || 'Ранг' }}
                  </option>
                </select>
              </div>

              <!-- 3D Card Flipper in Preview -->
              <div class="card-perspective w-full max-w-sm mx-auto">
                <div
                  class="card-flipper hover:scale-[1.01] active:scale-[0.99] transition-transform duration-200"
                  :class="{ 'is-flipped': previewFlipped }"
                  @click="previewFlipped = !previewFlipped"
                >
                  <!-- Front Face Preview -->
                  <div
                    class="card-face card-front relative rounded-3xl p-5 text-white overflow-hidden flex flex-col justify-between min-h-[260px] border border-white/20 select-none shadow-2xl"
                    :style="previewCardStyle"
                  >
                    <div class="absolute -top-16 -left-16 w-40 h-40 rounded-full bg-white/15 blur-2xl pointer-events-none"></div>
                    <div class="absolute -bottom-16 -right-16 w-40 h-40 rounded-full bg-black/35 blur-2xl pointer-events-none"></div>

                    <!-- Top row -->
                    <div class="relative z-10 flex items-center justify-between">
                      <div class="flex items-center gap-2">
                        <div class="w-7 h-7 rounded-lg bg-white/20 backdrop-blur-md border border-white/30 flex items-center justify-center font-black text-xs text-white">
                          {{ (form.name || 'R').charAt(0) }}
                        </div>
                        <span class="text-xs font-bold tracking-wider uppercase truncate opacity-95">
                          {{ form.name || 'Название заведения' }}
                        </span>
                      </div>
                      <span class="text-[10px] uppercase font-mono px-2.5 py-0.5 bg-black/35 backdrop-blur-sm rounded-full border border-white/15 text-white/90 font-bold">
                        {{ activePreviewTier?.badge || 'Loyalty Pass' }}
                      </span>
                    </div>

                    <!-- Chip & contactless -->
                    <div class="relative z-10 flex items-center justify-between my-2">
                      <div class="w-10 h-7 rounded-lg bg-gradient-to-br from-amber-300 via-amber-200 to-amber-500 border border-amber-600/40 p-1 flex flex-col justify-between shadow-inner">
                        <div class="w-full h-[1px] bg-amber-700/40"></div>
                        <div class="flex justify-between items-center px-1">
                          <div class="w-2 h-2.5 border border-amber-700/50 rounded-sm"></div>
                          <div class="w-2 h-2.5 border border-amber-700/50 rounded-sm"></div>
                        </div>
                        <div class="w-full h-[1px] bg-amber-700/40"></div>
                      </div>
                      <span class="text-white/60 text-xs font-mono">● ● ● ●</span>
                    </div>

                    <!-- Bottom row -->
                    <div class="relative z-10 space-y-1">
                      <div class="flex justify-between items-end">
                        <div>
                          <p class="text-[9px] uppercase text-white/70 font-semibold tracking-wider">Гость</p>
                          <p class="text-sm font-bold">Азамат Сериков</p>
                        </div>
                        <div class="text-right">
                          <p class="text-[9px] uppercase text-white/70 font-semibold tracking-wider">
                            {{ activePreviewTier?.cashback_percent ? `Кэшбэк ${activePreviewTier.cashback_percent}%` : 'Баланс' }}
                          </p>
                          <p class="text-lg font-black font-mono leading-none">1 500 <span class="text-xs font-bold opacity-85">₸</span></p>
                        </div>
                      </div>
                      <div class="pt-1.5 border-t border-white/20 flex items-center justify-between text-[10px] font-mono text-white/80">
                        <span>№ 7701 •••• 99</span>
                        <span>↺ Нажмите для QR</span>
                      </div>
                    </div>
                  </div>

                  <!-- Back Face Preview -->
                  <div
                    class="card-face card-back absolute inset-0 rounded-3xl p-5 text-white overflow-hidden flex flex-col justify-between min-h-[260px] border border-white/20 select-none shadow-2xl"
                    :style="previewCardStyle"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-xs font-bold uppercase tracking-wider">{{ form.name || 'Loyalty Pass' }}</span>
                      <span class="text-[10px] text-white/80">↺ Лицевая</span>
                    </div>

                    <div class="my-auto py-1 text-center">
                      <div class="bg-white rounded-2xl p-2.5 shadow-2xl inline-flex flex-col items-center justify-center border border-black/10">
                        <div class="w-24 h-24 bg-slate-900 rounded-lg flex items-center justify-center text-white text-3xl">
                          🏁
                        </div>
                        <span class="text-[10px] font-mono font-bold text-slate-900 mt-1">№ 77019990011</span>
                      </div>
                    </div>

                    <p class="text-[10px] text-white/90 text-center leading-tight">
                      Покажите QR-код кассиру для начисления или списания бонусов
                    </p>
                  </div>
                </div>
              </div>

              <!-- Wallet Banner Preview -->
              <div v-if="activePreviewTier?.banner_url" class="p-3.5 bg-slate-900/90 border border-slate-800 rounded-2xl space-y-2">
                <div class="flex items-center justify-between text-xs">
                  <span class="font-semibold text-white flex items-center gap-1.5">
                    <span> / G</span> Баннер ранга в Apple & Google Wallet
                  </span>
                  <span class="text-[10px] text-slate-400">1125 × 432 px</span>
                </div>
                <div class="w-full aspect-[2.6/1] rounded-xl overflow-hidden border border-slate-700/80 bg-black/40 shadow-inner">
                  <img :src="activePreviewTier.banner_url" alt="Tier Wallet Banner" class="w-full h-full object-cover" />
                </div>
                <p class="text-[10px] text-slate-400 text-center">
                  Этот баннер отображается в кошельке гостя при получении ранга «{{ activePreviewTier?.name }}»
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Save Button -->
        <div class="flex justify-end pt-5 border-t border-slate-800">
          <SaveButton :saving="saving" @save="saveSettings" />
        </div>
      </div>

      <!-- TAB: Onboarding -->
      <div v-show="activeTab === 'onboarding'" class="space-y-6">
        <!-- Main header / toggle box -->
        <div class="bg-slate-900 rounded-2xl border border-slate-800 p-6 space-y-6">
          <div class="flex items-center justify-between border-b border-slate-800 pb-5">
            <div>
              <div class="flex items-center gap-2">
                <span class="text-2xl">🚀</span>
                <h2 class="text-lg font-bold text-white">Страница онбординга (Веб-регистрация)</h2>
                <span class="px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  Web / QR
                </span>
              </div>
              <p class="text-slate-400 text-sm mt-1">
                Публичная мобильная веб-страница регистрации гостей без Telegram с выпуском карт в Apple Wallet и Google Wallet
              </p>
            </div>
            
            <!-- Toggle with WABA check -->
            <label class="relative inline-flex items-center cursor-pointer">
              <input
                id="toggle-web-onboarding"
                type="checkbox"
                :checked="form.is_web_onboarding_enabled"
                @click.prevent="toggleWebOnboarding"
                class="sr-only peer"
              >
              <div class="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
              <span class="ml-3 text-sm font-medium" :class="form.is_web_onboarding_enabled ? 'text-emerald-400' : 'text-slate-500'">
                {{ form.is_web_onboarding_enabled ? 'Включено' : 'Выключено' }}
              </span>
            </label>
          </div>

          <!-- WABA Warning Banner (if not configured) -->
          <div v-if="!isWabaConfigured" class="bg-amber-950/40 border border-amber-600/60 rounded-2xl p-5 flex items-start gap-4 shadow-lg shadow-amber-950/20">
            <div class="w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center text-amber-400 text-xl shrink-0">
              ⚠️
            </div>
            <div class="flex-1 space-y-1.5">
              <h4 class="text-white font-semibold text-sm">Интеграция с WhatsApp (WABA) не настроена!</h4>
              <p class="text-amber-200/90 text-xs leading-relaxed">
                Для работы страницы онбординга обязательно требуется настроенный и включенный WhatsApp Business API (WABA).
                Система отправляет проверочные коды регистрации гостям через WhatsApp.
                Пока WABA не настроена, тумблер страницы онбординга не может быть включен.
              </p>
              <div class="pt-2">
                <button
                  type="button"
                  @click="activeTab = 'waba'"
                  class="inline-flex items-center gap-2 px-3.5 py-1.5 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-semibold shadow-md transition-all cursor-pointer"
                >
                  <span>💬</span> Перейти в настройки WABA →
                </button>
              </div>
            </div>
          </div>

          <!-- Status alert when enabled -->
          <div v-else-if="form.is_web_onboarding_enabled" class="bg-emerald-950/40 border border-emerald-600/40 rounded-2xl p-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <span class="text-emerald-400 text-xl">✓</span>
              <div>
                <p class="text-white text-sm font-medium">Страница онбординга активна и готова принимать гостей</p>
                <p class="text-emerald-300/80 text-xs mt-0.5">WABA настроена для отправки OTP-кодов</p>
              </div>
            </div>
            <a
              :href="onboardingUrl"
              target="_blank"
              class="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all"
            >
              <span>↗</span> Открыть страницу
            </a>
          </div>

          <!-- Link & QR Code Box -->
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-2">
            <!-- Link and details (2 cols) -->
            <div class="lg:col-span-2 space-y-4">
              <div>
                <label class="form-label">Индивидуальная ссылка онбординга заведения</label>
                <div class="flex items-center gap-2">
                  <div class="relative flex-1">
                    <input
                      :value="onboardingUrl"
                      type="text"
                      readonly
                      class="form-input font-mono text-xs pr-10 bg-slate-950 text-indigo-300 border-slate-700"
                    />
                  </div>
                  <button
                    type="button"
                    @click="copyOnboardingUrl"
                    class="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer whitespace-nowrap"
                  >
                    <span>📋</span> Скопировать
                  </button>
                  <a
                    :href="onboardingUrl"
                    target="_blank"
                    class="px-4 py-2.5 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap"
                  >
                    <span>↗</span> Тест
                  </a>
                </div>
                <p class="text-xs text-slate-500 mt-1.5">
                  Slug заведения (<span class="font-mono text-indigo-400">{{ form.slug }}</span>) однозначно идентифицирует заведение в базе данных.
                </p>
              </div>

              <!-- Banner upload -->
              <div class="pt-2">
                <label class="form-label">Баннер страницы онбординга (Шапка)</label>
                <div class="flex items-start gap-5">
                  <!-- Banner preview -->
                  <div class="w-48 h-28 rounded-xl border border-slate-700 bg-slate-950 overflow-hidden relative flex items-center justify-center flex-shrink-0">
                    <img
                      v-if="form.web_onboarding_settings?.banner_url || onboardingBannerPreview"
                      :src="onboardingBannerPreview || form.web_onboarding_settings?.banner_url"
                      alt="Баннер онбординга"
                      class="w-full h-full object-cover"
                    />
                    <div v-else class="text-slate-600 text-xs text-center p-2">
                      <span class="text-xl block mb-1">🖼</span>
                      Баннер не загружен
                    </div>
                  </div>

                  <!-- Upload controls -->
                  <div class="space-y-2">
                    <label class="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold transition-all cursor-pointer shadow-md">
                      <span v-if="uploadingOnboardingBanner" class="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                      <span v-else>📤</span>
                      {{ form.web_onboarding_settings?.banner_url ? 'Заменить баннер' : 'Загрузить баннер' }}
                      <input
                        type="file"
                        accept="image/png,image/jpeg,image/webp"
                        class="hidden"
                        @change="uploadOnboardingBanner"
                        :disabled="uploadingOnboardingBanner"
                      />
                    </label>
                    <p class="text-[11px] text-slate-400 leading-relaxed">
                      Рекомендуемый размер: 1200×600 px (2:1). Форматы: PNG, JPG, WebP. Отображается в верхней части экрана смартфона.
                    </p>
                  </div>
                </div>
              </div>

              <!-- Accent color -->
              <div class="pt-2">
                <label class="form-label">Акцентный цвет кнопок и элементов</label>
                <div class="flex items-center gap-3">
                  <input
                    type="color"
                    v-model="onboardingAccentColor"
                    class="w-11 h-11 rounded-xl border border-slate-700 cursor-pointer bg-transparent p-0.5"
                  />
                  <input
                    type="text"
                    v-model="onboardingAccentColor"
                    class="form-input w-32 font-mono text-xs uppercase"
                  />
                </div>
              </div>
            </div>

            <!-- QR code card (1 col) -->
            <div class="bg-slate-950/80 border border-slate-800 rounded-2xl p-5 flex flex-col items-center justify-between text-center space-y-4">
              <div>
                <h3 class="text-white text-sm font-semibold">QR-код для гостей</h3>
                <p class="text-slate-400 text-xs mt-0.5">Печать на столы, тейбл-тенты и полиграфию</p>
              </div>

              <div class="p-3 bg-white rounded-2xl shadow-inner flex items-center justify-center">
                <img
                  v-if="qrCodeDataUrl"
                  :src="qrCodeDataUrl"
                  alt="QR Code"
                  class="w-44 h-44 object-contain"
                />
                <div v-else class="w-44 h-44 flex items-center justify-center text-slate-400 text-xs">
                  Генерация QR...
                </div>
              </div>

              <button
                type="button"
                @click="downloadQrCode"
                :disabled="!qrCodeDataUrl"
                class="w-full py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50"
              >
                <span>⬇</span> Скачать QR в PNG
              </button>
            </div>
          </div>

          <hr class="border-slate-800" />

          <!-- Bilingual texts configuration -->
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-white font-semibold text-sm">Тексты и приветствие (двуязычные)</h3>
                <p class="text-slate-400 text-xs">По умолчанию на странице отображается казахский язык (KZ), с возможностью мгновенного переключения на русский (RU)</p>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
              <!-- Kazakh Texts (Default) -->
              <div class="bg-slate-950/60 border border-slate-800/80 rounded-2xl p-4 space-y-3.5">
                <div class="flex items-center gap-2 border-b border-slate-800 pb-2">
                  <span class="text-sm font-bold text-indigo-400">🇰🇿 Қазақша (негізгі)</span>
                </div>
                <div>
                  <label class="form-label !text-xs">Басты тақырып (Заголовок)</label>
                  <input
                    v-model="onboardingTitleKz"
                    type="text"
                    class="form-input text-xs"
                    placeholder="Лоялдық картасын алыңыз"
                  />
                </div>
                <div>
                  <label class="form-label !text-xs">Қосымша мәтін (Подзаголовок)</label>
                  <input
                    v-model="onboardingSubtitleKz"
                    type="text"
                    class="form-input text-xs"
                    placeholder="Тіркеліп, әрбір тапсырыстан бонустар жинаңыз!"
                  />
                </div>
                <div>
                  <label class="form-label !text-xs">Қош келдіңіз бонусы (Текст о бонусе)</label>
                  <input
                    v-model="onboardingWelcomeBonusKz"
                    type="text"
                    class="form-input text-xs"
                    placeholder="Мысалы: Тіркелу үшін 500 бонус сыйлыққа!"
                  />
                </div>
              </div>

              <!-- Russian Texts -->
              <div class="bg-slate-950/60 border border-slate-800/80 rounded-2xl p-4 space-y-3.5">
                <div class="flex items-center gap-2 border-b border-slate-800 pb-2">
                  <span class="text-sm font-bold text-slate-300">🇷🇺 Русский</span>
                </div>
                <div>
                  <label class="form-label !text-xs">Главный заголовок</label>
                  <input
                    v-model="onboardingTitleRu"
                    type="text"
                    class="form-input text-xs"
                    placeholder="Получите карту лояльности"
                  />
                </div>
                <div>
                  <label class="form-label !text-xs">Подзаголовок</label>
                  <input
                    v-model="onboardingSubtitleRu"
                    type="text"
                    class="form-input text-xs"
                    placeholder="Зарегистрируйтесь и получайте бонусы с каждого заказа!"
                  />
                </div>
                <div>
                  <label class="form-label !text-xs">Приветственный бонус</label>
                  <input
                    v-model="onboardingWelcomeBonusRu"
                    type="text"
                    class="form-input text-xs"
                    placeholder="Например: 500 бонусов в подарок при регистрации!"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- Bottom Save bar -->
          <div class="flex justify-end pt-4 border-t border-slate-800">
            <SaveButton :saving="saving" @save="saveOnboardingSettings" />
          </div>
        </div>
      </div>

      <!-- TAB: Branding -->
      <div v-show="activeTab === 'branding'" class="bg-slate-900 rounded-2xl border border-slate-800 p-6 space-y-6">
        <!-- Color picker -->
        <div>
          <label class="form-label">Основной цвет бренда</label>
          <div class="flex items-center gap-4">
            <div class="relative">
              <input id="input-brand-color" type="color" v-model="brandColor"
                class="w-14 h-14 rounded-xl border-2 border-slate-700 cursor-pointer bg-transparent p-0.5" />
            </div>
            <input type="text" v-model="brandColor"
              class="form-input w-36 font-mono text-sm uppercase"
              placeholder="#6366f1"
              pattern="#[0-9a-fA-F]{6}"
              title="HEX формат #RRGGBB" />
            <div class="w-10 h-10 rounded-xl border border-slate-700 shadow-inner" :style="{ backgroundColor: brandColor }"></div>
          </div>
        </div>

        <!-- Greeting text -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="form-label">Приветственный текст (RU)</label>
            <input id="input-greeting" v-model="greetingText" type="text" class="form-input" placeholder="Добро пожаловать!" />
          </div>
          <div>
            <label class="form-label">Приветственный текст (KZ)</label>
            <input id="input-greeting-kz" v-model="greetingTextKz" type="text" class="form-input" placeholder="Қош келдіңіз!" />
          </div>
        </div>

        <!-- Logo upload -->
        <div>
          <label class="form-label">Логотип организации</label>
          <div class="flex items-center gap-4">
            <div class="w-20 h-20 bg-slate-800 rounded-xl border border-slate-700 overflow-hidden flex items-center justify-center flex-shrink-0">
              <img v-if="logoPreview || form.branding?.logo_url" :src="logoPreview || form.branding?.logo_url" class="w-full h-full object-cover" alt="Logo" />
              <span v-else class="text-slate-600 text-2xl">🖼</span>
            </div>
            <div>
              <label for="logo-upload" class="cursor-pointer bg-slate-800 hover:bg-slate-700 border border-slate-600 text-white px-4 py-2.5 rounded-xl text-sm font-medium transition-all inline-flex items-center gap-2">
                <span v-if="uploadingLogo" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                {{ uploadingLogo ? 'Загрузка...' : '📁 Выбрать файл' }}
              </label>
              <input id="logo-upload" type="file" accept="image/*" class="hidden" @change="uploadLogo" />
              <p class="text-xs text-slate-500 mt-1.5">PNG, JPG, WebP до 20MB</p>
            </div>
          </div>
        </div>

        <!-- Preview card -->
        <div>
          <label class="form-label">Предпросмотр карточки лояльности</label>
          <div class="w-full max-w-xs h-40 rounded-2xl p-5 shadow-xl flex flex-col justify-between"
            :style="{ background: `linear-gradient(135deg, ${brandColor}cc, ${brandColor}66)` }">
            <div class="flex justify-between items-start">
              <img v-if="logoPreview || form.branding?.logo_url" :src="logoPreview || form.branding?.logo_url" class="w-10 h-10 rounded-lg object-cover" alt="Logo" />
              <div v-else class="w-10 h-10 rounded-lg bg-white/20"></div>
              <span class="text-white/60 text-xs">Loyalty</span>
            </div>
            <div>
              <p class="text-white text-xs mb-1 opacity-70">{{ greetingText || 'Добро пожаловать!' }}</p>
              <p class="text-white font-bold text-lg">1 250 баллов</p>
            </div>
          </div>
        </div>

        <div class="flex justify-end pt-2">
          <SaveButton :saving="saving" @save="saveBranding" />
        </div>
      </div>
      

      <!-- TAB: Google Wallet -->
      <div v-show="activeTab === 'wallet'" class="bg-slate-900 rounded-2xl border border-slate-800 p-6 space-y-6">
        <!-- Toggle header -->
        <div class="flex items-center justify-between pb-6 border-b border-slate-800">
          <div>
            <div class="flex items-center gap-2">
              <span class="text-2xl">💳</span>
              <h2 class="text-lg font-bold text-white">Интеграция с Google Wallet</h2>
              <span class="px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Google Pay Passes
              </span>
            </div>
            <p class="text-slate-400 text-sm mt-1">
              Отображение кнопки добавления карты лояльности в кошелек Google Wallet для гостей в Telegram Mini App
            </p>
          </div>
          <label class="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" v-model="form.is_google_wallet_enabled" @change="toggleGoogleWallet" class="sr-only peer">
            <div class="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
            <span class="ml-3 text-sm font-medium" :class="form.is_google_wallet_enabled ? 'text-emerald-400' : 'text-slate-500'">
              {{ form.is_google_wallet_enabled ? 'Включено' : 'Выключено' }}
            </span>
          </label>
        </div>

        <div>
          <label class="form-label">Google Issuer ID</label>
          <input v-model="walletForm.issuer_id" type="text" class="form-input" placeholder="Например: 3388000000000000000" />
          <p class="text-xs text-slate-500 mt-1">Идентификатор эмитента из Google Pay & Wallet Console</p>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="form-label">Название программы (Loyalty Class)</label>
            <input v-model="walletForm.class_name" type="text" class="form-input" placeholder="Например: Ресторан Ромашка" />
          </div>
          <div>
            <label class="form-label">Имя издателя (Issuer Name)</label>
            <input v-model="walletForm.issuer_name" type="text" class="form-input" placeholder="Например: ООО Ромашка" />
          </div>
        </div>
        <!-- Logo -->
        <div>
          <label class="form-label">Логотип карты (Logo)</label>
          <div class="flex items-center gap-3 mb-2">
            <input v-model="walletForm.logo_url" type="text" class="form-input flex-1" placeholder="https://... или загрузите файл с компьютера" />
            <label class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-sm font-medium transition-colors cursor-pointer flex items-center gap-2 whitespace-nowrap">
              <span v-if="uploadingWalletLogo" class="w-4 h-4 border-2 border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin"></span>
              <span v-else>📁</span>
              {{ uploadingWalletLogo ? 'Загрузка...' : 'Загрузить PNG' }}
              <input type="file" accept="image/png,image/jpeg,image/webp" class="hidden" @change="uploadWalletLogo" :disabled="uploadingWalletLogo" />
            </label>
          </div>
          <p class="text-xs text-slate-500">
            Квадратное фото (PNG), мин. 660×660 px. В Google Wallet отображается в круглом бейдже вверху карты. Если не задано, берется логотип из вкладки Брендинг.
          </p>
          <div v-if="walletLogoPreview || walletForm.logo_url" class="mt-3 flex items-center gap-4 p-3 bg-slate-950/60 rounded-xl border border-slate-800 w-fit">
            <div class="relative w-16 h-16 rounded-full overflow-hidden border-2 border-indigo-500/40 bg-slate-900 flex items-center justify-center shadow-lg">
              <img :src="walletLogoPreview || walletForm.logo_url" alt="Logo preview" class="w-full h-full object-cover" />
            </div>
            <div class="flex flex-col">
              <span class="text-xs text-slate-300 font-medium">Круглый бейдж Google Wallet</span>
              <span class="text-[10px] text-slate-500">Так логотип будет выглядеть на карте</span>
              <button type="button" @click="walletForm.logo_url = ''; walletLogoPreview = null" class="mt-1 text-xs text-rose-400 hover:text-rose-300 text-left bg-transparent border-none cursor-pointer p-0">
                ✕ Очистить логотип
              </button>
            </div>
          </div>
        </div>

        <!-- Banner / Hero Image -->
        <div>
          <label class="form-label">Баннер / Фото для украшения карты (Hero Image)</label>
          <div class="flex items-center gap-3 mb-2">
            <input v-model="walletForm.hero_image_url" type="text" class="form-input flex-1" placeholder="https://... или загрузите файл с компьютера" />
            <label class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-sm font-medium transition-colors cursor-pointer flex items-center gap-2 whitespace-nowrap">
              <span v-if="uploadingBanner" class="w-4 h-4 border-2 border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin"></span>
              <span v-else>📁</span>
              {{ uploadingBanner ? 'Загрузка...' : 'Загрузить PNG/JPG' }}
              <input type="file" accept="image/png,image/jpeg,image/webp" class="hidden" @change="uploadBanner" :disabled="uploadingBanner" />
            </label>
          </div>
          <p class="text-xs text-slate-500">
            Широкий баннер по центру карты прямо над балансом (рекомендуется PNG или JPG, 1032 × 336 px, соотношение 3:1). Украшает карту фото интерьера, блюд или паттерном бренда.
          </p>
          <div v-if="bannerPreview || walletForm.hero_image_url" class="mt-3 relative rounded-xl overflow-hidden border border-slate-700 bg-slate-950 max-w-md h-28 flex items-center justify-center">
            <img :src="bannerPreview || walletForm.hero_image_url" alt="Hero banner preview" class="w-full h-full object-cover" />
            <button type="button" @click="walletForm.hero_image_url = ''; bannerPreview = null" class="absolute top-2 right-2 bg-black/60 hover:bg-black/80 text-white rounded-full p-1 text-xs transition-colors">
              ✕
            </button>
          </div>
        </div>

        <div>
          <label class="form-label">Цвет фона карты (HEX)</label>
          <div class="flex items-center gap-4">
            <input type="color" v-model="walletForm.hex_background_color" class="w-14 h-14 rounded-xl border-2 border-slate-700 cursor-pointer bg-transparent p-0.5" />
            <input type="text" v-model="walletForm.hex_background_color" class="form-input w-36 font-mono text-sm uppercase" placeholder="#000000" />
          </div>
        </div>
        <div class="flex items-center justify-between pt-4 border-t border-slate-800">
          <button
            type="button"
            @click="openWalletAdvancedModal"
            class="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-sm font-semibold flex items-center gap-2 transition-all cursor-pointer shadow-sm active:scale-95"
          >
            <span>⚙️</span>
            <span>Геолокация и Push-уведомления</span>
            <span v-if="walletForm.locations?.length" class="px-2 py-0.5 rounded-full text-xs bg-indigo-500/30 text-indigo-300 font-bold border border-indigo-500/30">
              {{ walletForm.locations.length }}
            </span>
          </button>
          <SaveButton :saving="syncingWallet" @save="syncWalletClass" />
        </div>

        <!-- Modal: Google Wallet Advanced (Geofencing & Bilingual Push) -->
        <div v-if="showWalletAdvancedModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 select-none">
          <div class="bg-slate-950 border border-slate-800 rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[88vh] animate-[scaleIn_0.2s_ease-out]">
            
            <!-- Modal Header -->
            <div class="px-6 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/90 flex-shrink-0">
              <div class="flex items-center gap-2.5">
                <span class="text-xl">⚙️</span>
                <div>
                  <h3 class="text-base font-bold text-white leading-tight">
                    Геолокация и Push-уведомления Google Wallet
                  </h3>
                  <p class="text-[11px] text-slate-400 mt-0.5 leading-tight">
                    Настройка гео-напоминаний на экране блокировки и шаблонов пушей
                  </p>
                </div>
              </div>
              <button 
                @click="showWalletAdvancedModal = false" 
                class="text-slate-400 hover:text-white transition-colors bg-transparent border-none cursor-pointer text-lg p-1"
              >
                ✕
              </button>
            </div>

            <!-- Modal Info Banner with Google limits -->
            <div class="px-6 py-3 bg-indigo-950/30 border-b border-indigo-900/40 flex-shrink-0">
              <div class="flex items-start gap-2.5 text-xs text-indigo-200/90 leading-relaxed">
                <span class="text-base flex-shrink-0">ℹ️</span>
                <div class="space-y-0.5">
                  <p><span class="font-bold text-indigo-300">Ограничения Google Wallet API:</span> гео-напоминания (макс. 10 точек, радиус ~150 м). Заголовок push-сообщения — <span class="font-bold text-amber-300">до 35 символов</span>, текст — <span class="font-bold text-amber-300">до 200 символов</span>.</p>
                  <p class="text-[11px] text-indigo-300/70">
                    Переменные: <code class="px-1 py-0.5 rounded bg-indigo-900/50 text-indigo-200">{balance}</code> (баланс), <code class="px-1 py-0.5 rounded bg-indigo-900/50 text-indigo-200">{change}</code> (изменение), <code class="px-1 py-0.5 rounded bg-indigo-900/50 text-indigo-200">{org_name}</code> (ресторан), <code class="px-1 py-0.5 rounded bg-indigo-900/50 text-indigo-200">{name}</code> (имя).
                  </p>
                </div>
              </div>
            </div>

            <!-- Modal Navigation Tabs -->
            <div class="flex border-b border-slate-800 bg-slate-900/50 px-6 gap-2 pt-2 flex-shrink-0">
              <button
                type="button"
                @click="activeWalletModalTab = 'geo'"
                class="px-4 py-2 text-xs font-bold rounded-t-xl transition-all border-b-2 flex items-center gap-1.5 cursor-pointer"
                :class="activeWalletModalTab === 'geo' 
                  ? 'border-indigo-500 text-indigo-300 bg-slate-900' 
                  : 'border-transparent text-slate-400 hover:text-slate-200 bg-transparent'"
              >
                <span>📍 Геоточки филиалов</span>
                <span class="px-1.5 py-0.2 rounded-full text-[10px] bg-indigo-500/20 text-indigo-300">
                  {{ walletForm.locations?.length || 0 }}/10
                </span>
              </button>
              <button
                type="button"
                @click="activeWalletModalTab = 'push'"
                class="px-4 py-2 text-xs font-bold rounded-t-xl transition-all border-b-2 flex items-center gap-1.5 cursor-pointer"
                :class="activeWalletModalTab === 'push' 
                  ? 'border-indigo-500 text-indigo-300 bg-slate-900' 
                  : 'border-transparent text-slate-400 hover:text-slate-200 bg-transparent'"
              >
                <span>🔔 Шаблоны Push-сообщений</span>
                <span class="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-800 text-slate-300">
                  RU / KZ
                </span>
              </button>
            </div>

            <!-- Modal Scrollable Content Body -->
            <div class="p-6 overflow-y-auto space-y-5 flex-1">
              
              <!-- TAB 1: Locations (Geofencing) -->
              <div v-show="activeWalletModalTab === 'geo'" class="space-y-4">
                
                <!-- Add new location form -->
                <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
                  <span class="text-xs font-bold text-slate-200 uppercase tracking-wider block">
                    Добавить новый ресторан / филиал
                  </span>
                  <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div>
                      <label class="block text-[11px] font-semibold text-slate-400 mb-1">Название филиала</label>
                      <input 
                        v-model="newLocation.name" 
                        type="text" 
                        class="form-input text-xs" 
                        placeholder="Например: Dostyk Plaza" 
                      />
                    </div>
                    <div>
                      <label class="block text-[11px] font-semibold text-slate-400 mb-1">Широта (Latitude, -90..90)</label>
                      <input 
                        v-model="newLocation.latitude" 
                        type="number" 
                        step="any" 
                        class="form-input text-xs font-mono" 
                        placeholder="43.238949" 
                      />
                    </div>
                    <div>
                      <label class="block text-[11px] font-semibold text-slate-400 mb-1">Долгота (Longitude, -180..180)</label>
                      <input 
                        v-model="newLocation.longitude" 
                        type="number" 
                        step="any" 
                        class="form-input text-xs font-mono" 
                        placeholder="76.889709" 
                      />
                    </div>
                  </div>
                  <div class="flex justify-between items-center pt-1">
                    <span class="text-[11px] text-slate-500">
                      Координаты можно скопировать в Яндекс или Google Maps
                    </span>
                    <button
                      type="button"
                      @click="addLocation"
                      :disabled="walletForm.locations?.length >= 10"
                      class="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 border-none cursor-pointer shadow-sm"
                    >
                      <span>➕</span>
                      <span>Добавить филиал</span>
                    </button>
                  </div>
                </div>

                <!-- Locations List -->
                <div>
                  <div class="flex justify-between items-center mb-2">
                    <span class="text-xs font-bold text-slate-300">
                      Список добавленных филиалов ({{ walletForm.locations?.length || 0 }} из 10)
                    </span>
                  </div>

                  <div v-if="!walletForm.locations || walletForm.locations.length === 0" class="text-center py-8 px-4 rounded-xl border border-dashed border-slate-800 bg-slate-900/30">
                    <span class="text-2xl block mb-1">📍</span>
                    <p class="text-xs text-slate-400 font-medium">Геоточки пока не добавлены</p>
                    <p class="text-[11px] text-slate-500 mt-0.5">Добавьте координаты, чтобы карта появлялась на экране блокировки гостей</p>
                  </div>

                  <div v-else class="space-y-2">
                    <div 
                      v-for="(loc, idx) in walletForm.locations" 
                      :key="idx"
                      class="p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between gap-3 group hover:border-slate-700 transition-all"
                    >
                      <div class="flex items-center gap-3 min-w-0">
                        <span class="w-6 h-6 rounded-full bg-indigo-500/20 text-indigo-300 flex items-center justify-center text-xs font-bold flex-shrink-0">
                          {{ idx + 1 }}
                        </span>
                        <div class="min-w-0 text-left">
                          <p class="text-xs font-bold text-white truncate leading-tight">
                            {{ loc.name || `Филиал #${idx + 1}` }}
                          </p>
                          <p class="text-[11px] text-slate-400 font-mono mt-0.5 leading-tight">
                            Широта: {{ loc.latitude }}, Долгота: {{ loc.longitude }}
                          </p>
                        </div>
                      </div>
                      <button
                        type="button"
                        @click="removeLocation(idx)"
                        class="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors border-none bg-transparent cursor-pointer flex-shrink-0"
                        title="Удалить филиал"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                </div>

              </div>

              <!-- TAB 2: Bilingual Push Notification Templates -->
              <div v-show="activeWalletModalTab === 'push'" class="space-y-4">
                
                <!-- Language Toggle Capsule -->
                <div class="flex items-center justify-between">
                  <span class="text-xs font-bold text-slate-300">Язык уведомления гостя:</span>
                  <div class="bg-slate-900 border border-slate-800 rounded-lg p-1 flex gap-1">
                    <button
                      type="button"
                      @click="activePushLang = 'ru'"
                      class="px-3 py-1 rounded-md text-xs font-bold transition-all border-none cursor-pointer"
                      :class="activePushLang === 'ru' ? 'bg-indigo-600 text-white shadow-sm' : 'bg-transparent text-slate-400 hover:text-slate-200'"
                    >
                      🇷🇺 Русский (RU)
                    </button>
                    <button
                      type="button"
                      @click="activePushLang = 'kz'"
                      class="px-3 py-1 rounded-md text-xs font-bold transition-all border-none cursor-pointer"
                      :class="activePushLang === 'kz' ? 'bg-indigo-600 text-white shadow-sm' : 'bg-transparent text-slate-400 hover:text-slate-200'"
                    >
                      🇰🇿 Қазақша (KZ)
                    </button>
                  </div>
                </div>

                <!-- Tag Pills Helper -->
                <div class="p-3 bg-slate-900/60 rounded-xl border border-slate-800 flex items-center gap-2 flex-wrap">
                  <span class="text-[11px] text-slate-400 font-medium">Быстрая вставка тега в текст:</span>
                  <button 
                    type="button" 
                    v-for="tag in ['{balance}', '{change}', '{org_name}', '{name}']" 
                    :key="tag"
                    @click="insertPushTag(tag)"
                    class="px-2 py-0.5 rounded-md bg-indigo-500/15 hover:bg-indigo-500/25 border border-indigo-500/30 text-indigo-300 text-[11px] font-mono cursor-pointer transition-all"
                  >
                    + {{ tag }}
                  </button>
                </div>

                <!-- RU Language Fields -->
                <div v-if="activePushLang === 'ru'" class="space-y-3 p-4 rounded-xl bg-slate-900/50 border border-slate-800">
                  <div>
                    <div class="flex justify-between items-center mb-1">
                      <label class="text-xs font-bold text-slate-200">Заголовок Push-уведомления (RU)</label>
                      <span 
                        class="text-[11px] font-mono"
                        :class="(walletForm.push_templates?.ru?.title?.length || 0) > 35 ? 'text-rose-400 font-bold' : 'text-slate-400'"
                      >
                        {{ walletForm.push_templates?.ru?.title?.length || 0 }} / 35
                      </span>
                    </div>
                    <input
                      v-model="walletForm.push_templates.ru.title"
                      type="text"
                      maxlength="35"
                      class="form-input text-xs"
                      placeholder="Баланс бонусов обновлен"
                    />
                  </div>

                  <div>
                    <div class="flex justify-between items-center mb-1">
                      <label class="text-xs font-bold text-slate-200">Текст сообщения Push-уведомления (RU)</label>
                      <span 
                        class="text-[11px] font-mono"
                        :class="(walletForm.push_templates?.ru?.body?.length || 0) > 200 ? 'text-rose-400 font-bold' : 'text-slate-400'"
                      >
                        {{ walletForm.push_templates?.ru?.body?.length || 0 }} / 200
                      </span>
                    </div>
                    <textarea
                      v-model="walletForm.push_templates.ru.body"
                      maxlength="200"
                      rows="3"
                      class="form-input text-xs resize-none"
                      placeholder="{org_name}: начислено +{change} бонусов! Баланс: {balance} б."
                    ></textarea>
                  </div>
                </div>

                <!-- KZ Language Fields -->
                <div v-if="activePushLang === 'kz'" class="space-y-3 p-4 rounded-xl bg-slate-900/50 border border-slate-800">
                  <div>
                    <div class="flex justify-between items-center mb-1">
                      <label class="text-xs font-bold text-slate-200">Push хабарламасының тақырыбы (KZ)</label>
                      <span 
                        class="text-[11px] font-mono"
                        :class="(walletForm.push_templates?.kz?.title?.length || 0) > 35 ? 'text-rose-400 font-bold' : 'text-slate-400'"
                      >
                        {{ walletForm.push_templates?.kz?.title?.length || 0 }} / 35
                      </span>
                    </div>
                    <input
                      v-model="walletForm.push_templates.kz.title"
                      type="text"
                      maxlength="35"
                      class="form-input text-xs"
                      placeholder="Бонус балансы жаңартылды"
                    />
                  </div>

                  <div>
                    <div class="flex justify-between items-center mb-1">
                      <label class="text-xs font-bold text-slate-200">Push хабарламасының мәтіні (KZ)</label>
                      <span 
                        class="text-[11px] font-mono"
                        :class="(walletForm.push_templates?.kz?.body?.length || 0) > 200 ? 'text-rose-400 font-bold' : 'text-slate-400'"
                      >
                        {{ walletForm.push_templates?.kz?.body?.length || 0 }} / 200
                      </span>
                    </div>
                    <textarea
                      v-model="walletForm.push_templates.kz.body"
                      maxlength="200"
                      rows="3"
                      class="form-input text-xs resize-none"
                      placeholder="{org_name}: +{change} бонус берілді! Балансыңыз: {balance} балл."
                    ></textarea>
                  </div>
                </div>

                <!-- Preview Box -->
                <div class="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                  <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
                    Пример отображения push-уведомления на смартфоне:
                  </span>
                  <div class="p-3 rounded-lg bg-zinc-900/90 border border-zinc-700/60 shadow-lg flex items-start gap-2.5">
                    <span class="text-lg">💳</span>
                    <div class="text-left min-w-0 flex-1">
                      <p class="text-xs font-bold text-white leading-tight">
                        {{ (activePushLang === 'kz' ? walletForm.push_templates?.kz?.title : walletForm.push_templates?.ru?.title) || 'Баланс бонусов обновлен' }}
                      </p>
                      <p class="text-[11px] text-zinc-300 mt-1 leading-snug">
                        {{ ((activePushLang === 'kz' ? walletForm.push_templates?.kz?.body : walletForm.push_templates?.ru?.body) || '{org_name}: начислено +{change} бонусов! Баланс: {balance} б.')
                            .replace('{balance}', '1 500')
                            .replace('{change}', '150')
                            .replace('{org_name}', form.name || 'Наш Ресторан')
                            .replace('{name}', 'Александр') }}
                      </p>
                    </div>
                  </div>
                </div>

              </div>

            </div>

            <!-- Modal Footer -->
            <div class="px-6 py-4 border-t border-slate-800 bg-slate-900/90 flex justify-end gap-3 flex-shrink-0">
              <button
                type="button"
                @click="showWalletAdvancedModal = false"
                class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-medium transition-colors border-none cursor-pointer"
              >
                Отмена
              </button>
              <button
                type="button"
                @click="saveWalletAdvancedSettings"
                :disabled="syncingWallet"
                class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 border-none cursor-pointer disabled:opacity-50 shadow-md"
              >
                <span v-if="syncingWallet" class="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                <span>Сохранить и синхронизировать</span>
              </button>
            </div>

          </div>
        </div>
      </div>

      <!-- TAB: Apple Wallet -->
      <div v-show="activeTab === 'apple_wallet'" class="bg-slate-900 rounded-2xl border border-slate-800 p-6 space-y-6">
        <!-- Header with Toggle -->
        <div class="flex items-center justify-between pb-6 border-b border-slate-800">
          <div>
            <div class="flex items-center gap-2">
              <span class="text-2xl">🍏</span>
              <h2 class="text-lg font-bold text-white">Интеграция с Apple Wallet</h2>
              <span class="px-2 py-0.5 rounded-full text-xs font-medium bg-zinc-700/50 text-zinc-300 border border-zinc-600/50">
                Apple Wallet Passes (iOS)
              </span>
            </div>
            <p class="text-slate-400 text-sm mt-1">
              Выпуск брендированных карт .pkpass с динамическим обновлением баланса и Push-уведомлениями по геолокации
            </p>
          </div>
          <label class="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" v-model="form.is_apple_wallet_enabled" @change="toggleAppleWallet" class="sr-only peer">
            <div class="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
            <span class="ml-3 text-sm font-medium" :class="form.is_apple_wallet_enabled ? 'text-emerald-400' : 'text-slate-500'">
              {{ form.is_apple_wallet_enabled ? 'Включено' : 'Выключено' }}
            </span>
          </label>
        </div>

        <!-- 2 Columns Grid: Left Settings / Right Card Live Preview -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          <!-- LEFT: Settings Form (7 cols) -->
          <div class="lg:col-span-7 space-y-5">
            
            <!-- Multi-tenant info banner -->
            <div class="p-4 rounded-xl bg-indigo-950/30 border border-indigo-900/40 text-xs text-indigo-200/90 space-y-1">
              <div class="flex items-center gap-2 font-bold text-indigo-300">
                <span>ℹ️</span>
                <span>Мультитенантная платформа (Single Issuer)</span>
              </div>
              <p class="text-indigo-200/80 leading-relaxed">
                Карты выпускаются под единым аккаунтом разработчика платформы. Заведению не нужен собственный аккаунт Apple. Если у заведения есть индивидуальный аккаунт Apple, укажите Pass ID и Team ID ниже.
              </p>
            </div>

            <!-- Pass ID & Team ID -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="form-label">Pass Type Identifier (Pass ID)</label>
                <input v-model="appleWalletForm.pass_type_id" type="text" class="form-input text-xs font-mono" placeholder="По умолчанию (из платформы)" />
                <p class="text-[11px] text-slate-500 mt-1">Оставьте пустым для мастер-эмитента</p>
              </div>
              <div>
                <label class="form-label">Apple Team ID</label>
                <input v-model="appleWalletForm.team_id" type="text" class="form-input text-xs font-mono" placeholder="По умолчанию (из платформы)" />
                <p class="text-[11px] text-slate-500 mt-1">10-значный ID команды разработчика</p>
              </div>
            </div>

            <!-- Program name -->
            <div>
              <label class="form-label">Название программы на карте</label>
              <input v-model="appleWalletForm.class_name" type="text" class="form-input" :placeholder="form.name || 'Например: Ресторан Del Mar'" />
              <p class="text-[11px] text-slate-500 mt-1">Отображается в заголовке карты рядом с логотипом</p>
            </div>

            <!-- Logo Upload -->
            <div>
              <label class="form-label">Логотип карты (Logo)</label>
              <div class="flex items-center gap-3 mb-2">
                <input v-model="appleWalletForm.logo_url" type="text" class="form-input flex-1 text-xs" placeholder="https://... или загрузите файл с компьютера" />
                <label class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-sm font-medium transition-colors cursor-pointer flex items-center gap-2 whitespace-nowrap">
                  <span v-if="uploadingAppleLogo" class="w-4 h-4 border-2 border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin"></span>
                  <span v-else>📁</span>
                  {{ uploadingAppleLogo ? 'Загрузка...' : 'Загрузить PNG' }}
                  <input type="file" accept="image/png,image/jpeg,image/webp" class="hidden" @change="uploadAppleLogo" :disabled="uploadingAppleLogo" />
                </label>
              </div>
              <p class="text-xs text-slate-500">
                Рекомендуется прозрачный PNG до 320 × 100 px. Отображается в левом верхнем углу карты. Если не задано, берётся логотип заведения.
              </p>
              <div v-if="appleLogoPreview || appleWalletForm.logo_url" class="mt-2.5 flex items-center gap-3 p-2.5 bg-slate-950/60 rounded-xl border border-slate-800 w-fit">
                <div class="h-10 px-3 py-1 bg-slate-900 rounded-lg border border-slate-800 flex items-center justify-center">
                  <img :src="appleLogoPreview || appleWalletForm.logo_url" alt="Apple logo preview" class="max-h-8 max-w-[120px] object-contain" />
                </div>
                <button type="button" @click="appleWalletForm.logo_url = ''; appleLogoPreview = null" class="text-xs text-rose-400 hover:text-rose-300 bg-transparent border-none cursor-pointer">
                  ✕ Удалить логотип
                </button>
              </div>
            </div>

            <!-- Strip Banner Upload -->
            <div>
              <label class="form-label">Баннер карты (Strip Image)</label>
              <div class="flex items-center gap-3 mb-2">
                <input v-model="appleWalletForm.strip_url" type="text" class="form-input flex-1 text-xs" placeholder="https://... или загрузите файл с компьютера" />
                <label class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-sm font-medium transition-colors cursor-pointer flex items-center gap-2 whitespace-nowrap">
                  <span v-if="uploadingAppleStrip" class="w-4 h-4 border-2 border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin"></span>
                  <span v-else>📁</span>
                  {{ uploadingAppleStrip ? 'Загрузка...' : 'Загрузить баннер' }}
                  <input type="file" accept="image/png,image/jpeg,image/webp" class="hidden" @change="uploadAppleStrip" :disabled="uploadingAppleStrip" />
                </label>
              </div>
              <p class="text-xs text-slate-500">
                Широкий баннер по центру карты (соотношение 3:1, 1125 × 369 px или 750 × 246 px). Фото интерьера, блюд или графический паттерн.
              </p>
              <div v-if="appleStripPreview || appleWalletForm.strip_url" class="mt-2.5 relative rounded-xl overflow-hidden border border-slate-800 bg-slate-950 max-w-md h-24 flex items-center justify-center">
                <img :src="appleStripPreview || appleWalletForm.strip_url" alt="Strip banner preview" class="w-full h-full object-cover" />
                <button type="button" @click="appleWalletForm.strip_url = ''; appleStripPreview = null" class="absolute top-2 right-2 bg-black/70 hover:bg-black/90 text-white rounded-full p-1 text-xs transition-colors">
                  ✕
                </button>
              </div>
            </div>

            <!-- Barcode Format Selection (Barcode vs QR) -->
            <div>
              <label class="form-label mb-2">Формат отображения кода на карте</label>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <!-- Option 1: Barcode (Code 128) - Default -->
                <label 
                  class="relative flex items-center p-3.5 rounded-xl border cursor-pointer transition-all select-none"
                  :class="appleWalletForm.barcode_type === 'barcode' ? 'bg-indigo-950/40 border-indigo-500/80 shadow-[0_0_15px_rgba(99,102,241,0.15)]' : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'"
                >
                  <input type="radio" value="barcode" v-model="appleWalletForm.barcode_type" class="sr-only" />
                  <div class="flex items-center gap-3 w-full">
                    <div class="w-10 h-10 rounded-lg flex items-center justify-center shrink-0" :class="appleWalletForm.barcode_type === 'barcode' ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/40' : 'bg-slate-800 text-slate-400 border border-slate-700'">
                      <svg viewBox="0 0 24 24" class="w-6 h-6 fill-current">
                        <rect x="2" y="4" width="2" height="16" />
                        <rect x="5" y="4" width="1" height="16" />
                        <rect x="7" y="4" width="3" height="16" />
                        <rect x="11" y="4" width="1" height="16" />
                        <rect x="13" y="4" width="2" height="16" />
                        <rect x="16" y="4" width="3" height="16" />
                        <rect x="20" y="4" width="2" height="16" />
                      </svg>
                    </div>
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2">
                        <span class="text-xs font-bold text-white">Штрих-код (Code 128)</span>
                        <span class="px-1.5 py-0.2 rounded text-[10px] font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">По умолчанию</span>
                      </div>
                      <p class="text-[11px] text-slate-400 mt-0.5">Линейный штрих-код для стандартных кассовых сканеров</p>
                    </div>
                    <div class="w-4 h-4 rounded-full border flex items-center justify-center shrink-0" :class="appleWalletForm.barcode_type === 'barcode' ? 'border-indigo-400 bg-indigo-500' : 'border-slate-600'">
                      <div v-if="appleWalletForm.barcode_type === 'barcode'" class="w-1.5 h-1.5 rounded-full bg-white"></div>
                    </div>
                  </div>
                </label>

                <!-- Option 2: QR Code -->
                <label 
                  class="relative flex items-center p-3.5 rounded-xl border cursor-pointer transition-all select-none"
                  :class="appleWalletForm.barcode_type === 'qr' ? 'bg-indigo-950/40 border-indigo-500/80 shadow-[0_0_15px_rgba(99,102,241,0.15)]' : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'"
                >
                  <input type="radio" value="qr" v-model="appleWalletForm.barcode_type" class="sr-only" />
                  <div class="flex items-center gap-3 w-full">
                    <div class="w-10 h-10 rounded-lg flex items-center justify-center shrink-0" :class="appleWalletForm.barcode_type === 'qr' ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/40' : 'bg-slate-800 text-slate-400 border border-slate-700'">
                      <svg viewBox="0 0 24 24" class="w-6 h-6 fill-current">
                        <path d="M3 3h6v6H3V3zm2 2v2h2V5H5zm8-2h6v6h-6V3zm2 2v2h2V5h-2zM3 13h6v6H3v-6zm2 2v2h2v-2H5zm13-2h3v2h-3v-2zm-5 0h2v3h-2v-3zm3 3h3v3h-3v-3zm-3 2h2v1h-2v-1zm5 1h1v2h-1v-2zm-8-3h2v1h-2v-1zm0 3h3v1h-3v-1zm5 0h1v1h-1v-1z"/>
                      </svg>
                    </div>
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2">
                        <span class="text-xs font-bold text-white">QR-код</span>
                      </div>
                      <p class="text-[11px] text-slate-400 mt-0.5">Двумерный код для 2D-сканеров и мобильных камер</p>
                    </div>
                    <div class="w-4 h-4 rounded-full border flex items-center justify-center shrink-0" :class="appleWalletForm.barcode_type === 'qr' ? 'border-indigo-400 bg-indigo-500' : 'border-slate-600'">
                      <div v-if="appleWalletForm.barcode_type === 'qr'" class="w-1.5 h-1.5 rounded-full bg-white"></div>
                    </div>
                  </div>
                </label>
              </div>
            </div>

            <!-- Colors -->
            <div>
              <label class="form-label mb-2">Цветовая палитра карты Apple Wallet</label>
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div class="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5">
                  <span class="text-xs font-semibold text-slate-400 block">Фон карты</span>
                  <div class="flex items-center gap-2">
                    <input type="color" v-model="appleWalletForm.background_color" class="w-9 h-9 rounded-lg border border-slate-700 cursor-pointer bg-transparent p-0.5" />
                    <input type="text" v-model="appleWalletForm.background_color" class="form-input text-xs font-mono uppercase" placeholder="#18181B" />
                  </div>
                </div>
                <div class="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5">
                  <span class="text-xs font-semibold text-slate-400 block">Цвет текста</span>
                  <div class="flex items-center gap-2">
                    <input type="color" v-model="appleWalletForm.foreground_color" class="w-9 h-9 rounded-lg border border-slate-700 cursor-pointer bg-transparent p-0.5" />
                    <input type="text" v-model="appleWalletForm.foreground_color" class="form-input text-xs font-mono uppercase" placeholder="#FFFFFF" />
                  </div>
                </div>
                <div class="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5">
                  <span class="text-xs font-semibold text-slate-400 block">Цвет подписей</span>
                  <div class="flex items-center gap-2">
                    <input type="color" v-model="appleWalletForm.label_color" class="w-9 h-9 rounded-lg border border-slate-700 cursor-pointer bg-transparent p-0.5" />
                    <input type="text" v-model="appleWalletForm.label_color" class="form-input text-xs font-mono uppercase" placeholder="#94A3B8" />
                  </div>
                </div>
              </div>
            </div>

            <!-- Action buttons -->
            <div class="flex items-center justify-between pt-4 border-t border-slate-800">
              <button
                type="button"
                @click="openAppleAdvancedModal"
                class="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-sm font-semibold flex items-center gap-2 transition-all cursor-pointer shadow-sm active:scale-95"
              >
                <span>⚙️</span>
                <span>Геолокация и Push-уведомления</span>
                <span v-if="appleWalletForm.locations?.length" class="px-2 py-0.5 rounded-full text-xs bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30">
                  {{ appleWalletForm.locations.length }}
                </span>
              </button>
              <SaveButton :saving="savingAppleWallet" @save="saveAppleWalletSettings" />
            </div>

          </div>

          <!-- RIGHT: Interactive Card Live Preview (5 cols) -->
          <div class="lg:col-span-5 flex flex-col items-center">
            <div class="sticky top-6 w-full max-w-sm space-y-3">
              <div class="flex items-center justify-between px-1">
                <span class="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <span>📱</span> Предпросмотр карты Apple Wallet
                </span>
                <span class="text-[11px] text-emerald-400 font-medium">StoreCard iOS</span>
              </div>

              <!-- Pass Canvas Container -->
              <div 
                class="w-full rounded-[28px] p-5 shadow-2xl border border-white/10 transition-all duration-300 relative overflow-hidden flex flex-col justify-between"
                :style="{ backgroundColor: appleWalletForm.background_color || '#18181b', minHeight: '380px' }"
              >
                <!-- Top Row: Logo & Header Balance -->
                <div class="flex items-center justify-between gap-2 z-10">
                  <div class="flex items-center gap-2.5 min-w-0">
                    <img 
                      v-if="appleLogoPreview || appleWalletForm.logo_url" 
                      :src="appleLogoPreview || appleWalletForm.logo_url" 
                      alt="Logo" 
                      class="max-h-7 max-w-[100px] object-contain flex-shrink-0"
                    />
                    <span v-else class="text-xl">🍏</span>
                    <span 
                      class="font-bold text-sm truncate leading-tight" 
                      :style="{ color: appleWalletForm.foreground_color || '#ffffff' }"
                    >
                      {{ appleWalletForm.class_name || form.name || 'Ваш ресторан' }}
                    </span>
                  </div>
                  <div class="text-right flex-shrink-0">
                    <span 
                      class="block text-[10px] font-bold uppercase tracking-wider leading-none" 
                      :style="{ color: appleWalletForm.label_color || '#94a3b8' }"
                    >
                      БОНУСЫ
                    </span>
                    <span 
                      class="text-xl font-black leading-tight tracking-tight" 
                      :style="{ color: appleWalletForm.foreground_color || '#ffffff' }"
                    >
                      1 500
                    </span>
                  </div>
                </div>

                <!-- Middle Strip Banner -->
                <div class="my-3 rounded-2xl overflow-hidden border border-black/20 h-28 bg-black/20 flex items-center justify-center relative shadow-inner">
                  <img 
                    v-if="appleStripPreview || appleWalletForm.strip_url" 
                    :src="appleStripPreview || appleWalletForm.strip_url" 
                    alt="Strip Banner" 
                    class="w-full h-full object-cover"
                  />
                  <div v-else class="w-full h-full flex items-center justify-center bg-gradient-to-tr from-black/40 via-white/5 to-white/10 text-center px-4">
                    <span class="text-xs font-semibold text-white/50">Баннер-полоса карты (Strip)</span>
                  </div>
                </div>

                <!-- Secondary Fields Row (Guest & Status) -->
                <div class="grid grid-cols-2 gap-2 py-1 z-10">
                  <div>
                    <span 
                      class="block text-[10px] font-bold uppercase tracking-wider leading-none" 
                      :style="{ color: appleWalletForm.label_color || '#94a3b8' }"
                    >
                      ГОСТЬ
                    </span>
                    <span 
                      class="text-xs font-bold leading-tight block truncate mt-0.5" 
                      :style="{ color: appleWalletForm.foreground_color || '#ffffff' }"
                    >
                      Алихан Нурланов
                    </span>
                  </div>
                  <div class="text-right">
                    <span 
                      class="block text-[10px] font-bold uppercase tracking-wider leading-none" 
                      :style="{ color: appleWalletForm.label_color || '#94a3b8' }"
                    >
                      СТАТУС
                    </span>
                    <span 
                      class="text-xs font-bold leading-tight block truncate mt-0.5 text-amber-300"
                    >
                      Gold (5% кэшбэк)
                    </span>
                  </div>
                </div>

                <!-- Barcode Container (White Apple Wallet Barcode Pad) -->
                <div class="mt-3 bg-white rounded-2xl p-3 shadow-lg flex flex-col items-center justify-center text-center transition-all">
                  <!-- QR Code Mode -->
                  <div v-if="appleWalletForm.barcode_type === 'qr'" class="w-20 h-20 bg-neutral-900 rounded-lg p-1.5 flex items-center justify-center shadow-inner">
                    <svg viewBox="0 0 24 24" class="w-full h-full text-white fill-current">
                      <path d="M3 3h6v6H3V3zm2 2v2h2V5H5zm8-2h6v6h-6V3zm2 2v2h2V5h-2zM3 13h6v6H3v-6zm2 2v2h2v-2H5zm13-2h3v2h-3v-2zm-5 0h2v3h-2v-3zm3 3h3v3h-3v-3zm-3 2h2v1h-2v-1zm5 1h1v2h-1v-2zm-8-3h2v1h-2v-1zm0 3h3v1h-3v-1zm5 0h1v1h-1v-1z"/>
                    </svg>
                  </div>

                  <!-- 1D Barcode (Code 128) Mode - Default -->
                  <div v-else class="w-full max-w-[220px] h-12 flex items-center justify-center py-1">
                    <svg viewBox="0 0 160 48" class="w-full h-full text-neutral-900 fill-current" preserveAspectRatio="none">
                      <rect x="0" y="0" width="3" height="48" />
                      <rect x="5" y="0" width="2" height="48" />
                      <rect x="9" y="0" width="4" height="48" />
                      <rect x="16" y="0" width="1" height="48" />
                      <rect x="19" y="0" width="3" height="48" />
                      <rect x="25" y="0" width="2" height="48" />
                      <rect x="29" y="0" width="5" height="48" />
                      <rect x="36" y="0" width="2" height="48" />
                      <rect x="40" y="0" width="1" height="48" />
                      <rect x="43" y="0" width="4" height="48" />
                      <rect x="49" y="0" width="2" height="48" />
                      <rect x="53" y="0" width="3" height="48" />
                      <rect x="58" y="0" width="1" height="48" />
                      <rect x="62" y="0" width="5" height="48" />
                      <rect x="69" y="0" width="2" height="48" />
                      <rect x="73" y="0" width="2" height="48" />
                      <rect x="77" y="0" width="4" height="48" />
                      <rect x="83" y="0" width="1" height="48" />
                      <rect x="86" y="0" width="3" height="48" />
                      <rect x="91" y="0" width="2" height="48" />
                      <rect x="95" y="0" width="5" height="48" />
                      <rect x="102" y="0" width="2" height="48" />
                      <rect x="106" y="0" width="1" height="48" />
                      <rect x="109" y="0" width="4" height="48" />
                      <rect x="115" y="0" width="2" height="48" />
                      <rect x="119" y="0" width="3" height="48" />
                      <rect x="124" y="0" width="2" height="48" />
                      <rect x="128" y="0" width="4" height="48" />
                      <rect x="134" y="0" width="1" height="48" />
                      <rect x="137" y="0" width="3" height="48" />
                      <rect x="142" y="0" width="2" height="48" />
                      <rect x="146" y="0" width="4" height="48" />
                      <rect x="153" y="0" width="2" height="48" />
                      <rect x="157" y="0" width="3" height="48" />
                    </svg>
                  </div>

                  <span class="text-xs font-mono font-bold text-neutral-800 tracking-widest mt-1">
                    9988776655
                  </span>
                </div>

              </div>

              <!-- Footer hint -->
              <p class="text-[11px] text-center text-slate-500 px-4">
                Карта полностью интерактивна. Гость с iPhone сможет добавить её в 1 клик на веб-странице или в TMA.
              </p>
            </div>
          </div>

        </div>

      </div>

      <!-- Modal: Apple Wallet Advanced (Geofencing & Bilingual Push) -->
      <div v-if="showAppleAdvancedModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 select-none">
        <div class="bg-slate-950 border border-slate-800 rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[88vh] animate-[scaleIn_0.2s_ease-out]">
          
          <!-- Modal Header -->
          <div class="px-6 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/90 flex-shrink-0">
            <div class="flex items-center gap-2.5">
              <span class="text-xl">⚙️</span>
              <div>
                <h3 class="text-base font-bold text-white leading-tight">
                  Геолокация и Push-уведомления Apple Wallet
                </h3>
                <p class="text-[11px] text-slate-400 mt-0.5 leading-tight">
                  Появление карты на экране блокировки iPhone при приближении к заведению и авто-пуши при изменении баланса
                </p>
              </div>
            </div>
            <button 
              @click="showAppleAdvancedModal = false" 
              class="text-slate-400 hover:text-white transition-colors bg-transparent border-none cursor-pointer text-lg p-1"
            >
              ✕
            </button>
          </div>

          <!-- Modal Info Banner with Apple limits -->
          <div class="px-6 py-3 bg-indigo-950/30 border-b border-indigo-900/40 flex-shrink-0">
            <div class="flex items-start gap-2.5 text-xs text-indigo-200/90 leading-relaxed">
              <span class="text-base flex-shrink-0">ℹ️</span>
              <div class="space-y-0.5">
                <p><span class="font-bold text-indigo-300">Возможности Apple PassKit:</span> до 10 геоточек филиалов. При приближении к координатам карта появляется на экране блокировки iPhone. В шаблоне обновления баланса используйте <code class="px-1 py-0.5 rounded bg-indigo-900/50 text-indigo-200">%@</code> (Apple подставит новое количество бонусов).</p>
              </div>
            </div>
          </div>

          <!-- Modal Navigation Tabs -->
          <div class="flex border-b border-slate-800 bg-slate-900/50 px-6 gap-2 pt-2 flex-shrink-0">
            <button
              type="button"
              @click="activeAppleModalTab = 'geo'"
              class="px-4 py-2 text-xs font-bold rounded-t-xl transition-all border-b-2 flex items-center gap-1.5 cursor-pointer"
              :class="activeAppleModalTab === 'geo' 
                ? 'border-indigo-500 text-indigo-300 bg-slate-900' 
                : 'border-transparent text-slate-400 hover:text-slate-200 bg-transparent'"
            >
              <span>📍 Геоточки филиалов</span>
              <span class="px-1.5 py-0.2 rounded-full text-[10px] bg-indigo-500/20 text-indigo-300">
                {{ appleWalletForm.locations?.length || 0 }}/10
              </span>
            </button>
            <button
              type="button"
              @click="activeAppleModalTab = 'push'"
              class="px-4 py-2 text-xs font-bold rounded-t-xl transition-all border-b-2 flex items-center gap-1.5 cursor-pointer"
              :class="activeAppleModalTab === 'push' 
                ? 'border-indigo-500 text-indigo-300 bg-slate-900' 
                : 'border-transparent text-slate-400 hover:text-slate-200 bg-transparent'"
            >
              <span>🔔 Шаблоны Push-уведомлений</span>
              <span class="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-800 text-slate-300">
                RU / KZ
              </span>
            </button>
          </div>

          <!-- Modal Scrollable Content Body -->
          <div class="p-6 overflow-y-auto space-y-5 flex-1">
            
            <!-- TAB 1: Locations (Geofencing) -->
            <div v-show="activeAppleModalTab === 'geo'" class="space-y-4">
              
              <!-- Add new location form -->
              <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
                <span class="text-xs font-bold text-slate-200 uppercase tracking-wider block">
                  Добавить новый ресторан / филиал
                </span>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div>
                    <label class="block text-[11px] font-semibold text-slate-400 mb-1">Название филиала</label>
                    <input 
                      v-model="newAppleLocation.name" 
                      type="text" 
                      class="form-input text-xs" 
                      placeholder="Например: Del Mar Dostyk" 
                    />
                  </div>
                  <div>
                    <label class="block text-[11px] font-semibold text-slate-400 mb-1">Широта (Latitude)</label>
                    <input 
                      v-model="newAppleLocation.latitude" 
                      type="number" 
                      step="any" 
                      class="form-input text-xs font-mono" 
                      placeholder="43.238949" 
                    />
                  </div>
                  <div>
                    <label class="block text-[11px] font-semibold text-slate-400 mb-1">Долгота (Longitude)</label>
                    <input 
                      v-model="newAppleLocation.longitude" 
                      type="number" 
                      step="any" 
                      class="form-input text-xs font-mono" 
                      placeholder="76.889709" 
                    />
                  </div>
                </div>
                <div>
                  <label class="block text-[11px] font-semibold text-slate-400 mb-1">Текст на экране блокировки iPhone при приближении</label>
                  <input 
                    v-model="newAppleLocation.relevant_text" 
                    type="text" 
                    class="form-input text-xs" 
                    placeholder="Например: Вы рядом с рестораном! Предъявите карту для бонусов." 
                  />
                </div>
                <div class="flex justify-between items-center pt-1">
                  <span class="text-[11px] text-slate-500">
                    Координаты можно скопировать из 2GIS, Яндекс или Google Maps
                  </span>
                  <button
                    type="button"
                    @click="addAppleLocation"
                    :disabled="appleWalletForm.locations?.length >= 10"
                    class="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 border-none cursor-pointer shadow-sm"
                  >
                    <span>➕</span>
                    <span>Добавить филиал</span>
                  </button>
                </div>
              </div>

              <!-- Locations List -->
              <div>
                <div class="flex justify-between items-center mb-2">
                  <span class="text-xs font-bold text-slate-300">
                    Список добавленных филиалов ({{ appleWalletForm.locations?.length || 0 }} из 10)
                  </span>
                </div>

                <div v-if="!appleWalletForm.locations || appleWalletForm.locations.length === 0" class="text-center py-8 px-4 rounded-xl border border-dashed border-slate-800 bg-slate-900/30">
                  <span class="text-2xl block mb-1">📍</span>
                  <p class="text-xs text-slate-400 font-medium">Геоточки пока не добавлены</p>
                  <p class="text-[11px] text-slate-500 mt-0.5">Добавьте координаты, чтобы карта появлялась на экране блокировки гостей</p>
                </div>

                <div v-else class="space-y-2">
                  <div 
                    v-for="(loc, idx) in appleWalletForm.locations" 
                    :key="idx"
                    class="p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between gap-3 group hover:border-slate-700 transition-all"
                  >
                    <div class="flex items-center gap-3 min-w-0">
                      <span class="w-6 h-6 rounded-full bg-indigo-500/20 text-indigo-300 flex items-center justify-center text-xs font-bold flex-shrink-0">
                        {{ idx + 1 }}
                      </span>
                      <div class="min-w-0 text-left">
                        <p class="text-xs font-bold text-white truncate leading-tight">
                          {{ loc.name || `Филиал #${idx + 1}` }}
                        </p>
                        <p class="text-[11px] text-slate-400 font-mono mt-0.5 leading-tight">
                          {{ loc.latitude }}, {{ loc.longitude }}
                        </p>
                        <p v-if="loc.relevant_text" class="text-[11px] text-indigo-300 mt-0.5 truncate">
                          💬 {{ loc.relevant_text }}
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      @click="removeAppleLocation(idx)"
                      class="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors border-none bg-transparent cursor-pointer flex-shrink-0"
                      title="Удалить филиал"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              </div>

            </div>

            <!-- TAB 2: Bilingual Push Notification Templates -->
            <div v-show="activeAppleModalTab === 'push'" class="space-y-4">
              
              <!-- Language Toggle Capsule -->
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-slate-300">Язык уведомления гостя:</span>
                <div class="bg-slate-900 border border-slate-800 rounded-lg p-1 flex gap-1">
                  <button
                    type="button"
                    @click="activeApplePushLang = 'ru'"
                    class="px-3 py-1 rounded-md text-xs font-bold transition-all border-none cursor-pointer"
                    :class="activeApplePushLang === 'ru' ? 'bg-indigo-600 text-white shadow-sm' : 'bg-transparent text-slate-400 hover:text-slate-200'"
                  >
                    🇷🇺 Русский (RU)
                  </button>
                  <button
                    type="button"
                    @click="activeApplePushLang = 'kz'"
                    class="px-3 py-1 rounded-md text-xs font-bold transition-all border-none cursor-pointer"
                    :class="activeApplePushLang === 'kz' ? 'bg-indigo-600 text-white shadow-sm' : 'bg-transparent text-slate-400 hover:text-slate-200'"
                  >
                    🇰🇿 Қазақша (KZ)
                  </button>
                </div>
              </div>

              <!-- Tag Pills Helper -->
              <div class="p-3 bg-slate-900/60 rounded-xl border border-slate-800 flex items-center gap-2 flex-wrap">
                <span class="text-[11px] text-slate-400 font-medium">Тег нового баланса:</span>
                <button 
                  type="button" 
                  @click="insertApplePushTag('%@')"
                  class="px-2 py-0.5 rounded-md bg-indigo-500/15 hover:bg-indigo-500/25 border border-indigo-500/30 text-indigo-300 text-[11px] font-mono cursor-pointer transition-all"
                >
                  + %@ (новое число баллов)
                </button>
              </div>

              <!-- RU Language Fields -->
              <div v-if="activeApplePushLang === 'ru'" class="space-y-3 p-4 rounded-xl bg-slate-900/50 border border-slate-800">
                <div>
                  <label class="block text-xs font-semibold text-slate-300 mb-1">
                    Текст пуш-уведомления об изменении баланса (Change Message)
                  </label>
                  <input
                    v-model="appleWalletForm.push_templates.ru.change_message"
                    type="text"
                    class="form-input text-xs"
                    placeholder="Баланс бонусов обновлен: %@ баллов"
                  />
                  <p class="text-[11px] text-slate-500 mt-1">
                    Символ <code class="text-indigo-400">%@</code> автоматически заменяется iOS на новый баланс гостя при начислении или списании.
                  </p>
                </div>
              </div>

              <!-- KZ Language Fields -->
              <div v-if="activeApplePushLang === 'kz'" class="space-y-3 p-4 rounded-xl bg-slate-900/50 border border-slate-800">
                <div>
                  <label class="block text-xs font-semibold text-slate-300 mb-1">
                    Бонус балансы өзгергендегі хабарлама (Change Message KZ)
                  </label>
                  <input
                    v-model="appleWalletForm.push_templates.kz.change_message"
                    type="text"
                    class="form-input text-xs"
                    placeholder="Бонус балансы жаңартылды: %@ балл"
                  />
                  <p class="text-[11px] text-slate-500 mt-1">
                    <code class="text-indigo-400">%@</code> белгісі жаңа бонус санымен автоматты түрде алмастырылады.
                  </p>
                </div>
              </div>

            </div>

          </div>

          <!-- Modal Footer -->
          <div class="px-6 py-3.5 border-t border-slate-800 bg-slate-900/90 flex justify-end gap-3 flex-shrink-0">
            <button
              type="button"
              @click="showAppleAdvancedModal = false"
              class="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors border-none cursor-pointer"
            >
              Отмена
            </button>
            <button
              type="button"
              @click="saveAppleAdvancedSettings"
              class="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-colors shadow-md flex items-center gap-1.5 border-none cursor-pointer"
            >
              <span>✓</span>
              <span>Сохранить параметры</span>
            </button>
          </div>

        </div>
      </div>

      <!-- TAB: Loyalty Programs -->
      <div v-show="activeTab === 'loyalty_programs'" class="bg-slate-900 rounded-2xl border border-slate-800 p-6 space-y-5">
        <div class="flex justify-between items-center mb-4">
          <div>
            <h2 class="text-lg font-bold text-white">Программа лояльности</h2>
            <p class="text-slate-400 text-xs">Управление разделами и информацией о программе лояльности для TMA</p>
          </div>
          <button @click="openCreateModal"
            class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors shadow-md flex items-center gap-1 border-none cursor-pointer">
            <span>➕</span> Создать
          </button>
        </div>

        <!-- Table -->
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="border-b border-slate-800 text-slate-400 text-xs font-semibold uppercase">
                <th class="py-3 px-4">Заголовок (RU)</th>
                <th class="py-3 px-4">Заголовок (KZ)</th>
                <th class="py-3 px-4">Описание (RU)</th>
                <th class="py-3 px-4">Описание (KZ)</th>
                <th class="py-3 px-4 text-right">Действие</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="programsLoading" class="border-b border-slate-850">
                <td colspan="5" class="py-8 text-center text-slate-500 text-sm">
                  Загрузка...
                </td>
              </tr>
              <tr v-else-if="programs.length === 0" class="border-b border-slate-850">
                <td colspan="5" class="py-8 text-center text-slate-500 text-sm">
                  Программы лояльности не созданы. Нажмите "Создать", чтобы добавить.
                </td>
              </tr>
              <tr v-else v-for="prog in programs" :key="prog.id" class="border-b border-slate-800 hover:bg-slate-800/20 text-sm text-slate-200">
                <td class="py-3.5 px-4 font-semibold text-white max-w-[120px] truncate" :title="prog.title">{{ prog.title }}</td>
                <td class="py-3.5 px-4 font-semibold text-white max-w-[120px] truncate" :title="prog.title_kz">{{ prog.title_kz || '-' }}</td>
                <td class="py-3.5 px-4 max-w-[200px] truncate text-slate-400" :title="prog.description">{{ prog.description }}</td>
                <td class="py-3.5 px-4 max-w-[200px] truncate text-slate-400" :title="prog.description_kz">{{ prog.description_kz || '-' }}</td>
                <td class="py-3.5 px-4 text-right space-x-3 text-base">
                  <button @click="openEditModal(prog)" class="text-indigo-400 hover:text-indigo-300 font-medium transition-colors bg-transparent border-none cursor-pointer" title="Редактировать">
                    ✏️
                  </button>
                  <button @click="confirmDelete(prog)" class="text-rose-400 hover:text-rose-300 font-medium transition-colors bg-transparent border-none cursor-pointer" title="Удалить">
                    🗑️
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Create/Edit Modal -->
        <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div class="bg-slate-950 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden animate-[scaleIn_0.2s_ease-out]">
            <div class="px-6 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-900">
              <h3 class="text-lg font-bold text-white">
                {{ modalMode === 'create' ? 'Создать программу лояльности' : 'Редактировать программу лояльности' }}
              </h3>
              <button @click="showModal = false" class="text-slate-400 hover:text-white transition-colors bg-transparent border-none cursor-pointer text-lg">✕</button>
            </div>
            <div class="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
              <div>
                <label class="form-label">Заголовок (RU)</label>
                <input v-model="modalForm.title" type="text" class="form-input" placeholder="Введите заголовок на русском..." />
              </div>
              <div>
                <label class="form-label">Заголовок (KZ)</label>
                <input v-model="modalForm.title_kz" type="text" class="form-input" placeholder="Введите заголовок на казахском..." />
              </div>
              <div>
                <label class="form-label">Описание (RU)</label>
                <textarea v-model="modalForm.description" class="form-input min-h-[100px] resize-none" placeholder="Введите описание программы на русском..."></textarea>
              </div>
              <div>
                <label class="form-label">Описание (KZ)</label>
                <textarea v-model="modalForm.description_kz" class="form-input min-h-[100px] resize-none" placeholder="Введите описание программы на казахском..."></textarea>
              </div>
            </div>
            <div class="px-6 py-4 border-t border-slate-800 bg-slate-900 flex justify-end gap-3">
              <button @click="showModal = false" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-medium transition-colors border-none cursor-pointer">
                Отмена
              </button>
              <button @click="saveProgram" :disabled="submittingProgram"
                class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 border-none cursor-pointer disabled:opacity-50">
                <span v-if="submittingProgram" class="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                Сохранить
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Delete Confirmation Modal -->
        <div v-if="showDeleteConfirm" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div class="bg-slate-950 border border-slate-800 rounded-2xl w-full max-w-sm shadow-2xl overflow-hidden animate-[scaleIn_0.2s_ease-out]">
            <div class="p-6 text-center space-y-4">
              <div class="text-4xl text-rose-500">⚠️</div>
              <h3 class="text-lg font-bold text-white">Удалить запись?</h3>
              <p class="text-slate-400 text-sm">Вы уверены, что хотите удалить программу лояльности "{{ programToDelete?.title }}"? Это действие необратимо.</p>
            </div>
            <div class="px-6 py-4 border-t border-slate-800 bg-slate-900 flex justify-center gap-3">
              <button @click="showDeleteConfirm = false" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-medium transition-colors border-none cursor-pointer">
                Отмена
              </button>
              <button @click="deleteProgram" :disabled="deletingProgram"
                class="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 border-none cursor-pointer disabled:opacity-50">
                <span v-if="deletingProgram" class="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                Удалить
              </button>
            </div>
          </div>
        </div>

        <!-- Test Delivery Modal -->
        <div v-if="testModalOpen" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div class="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-md overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <!-- Modal header -->
            <div class="px-6 py-5 border-b border-slate-800 flex items-center justify-between">
              <h2 class="text-lg font-bold text-white">Тестовая отправка</h2>
              <button @click="closeTestModal" class="text-slate-400 hover:text-white text-lg bg-transparent border-none cursor-pointer">✕</button>
            </div>

            <!-- Modal body -->
            <div class="px-6 py-6 space-y-4">
              <div class="space-y-2">
                <label class="block text-sm font-semibold text-slate-300">Ваш Telegram ID</label>
                <input
                  v-model="testTelegramId"
                  type="text"
                  placeholder="Введите ваш Telegram ID"
                  class="w-full bg-slate-950 border border-slate-800 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent placeholder:text-slate-600 transition-all"
                />
              </div>

              <div class="text-xs text-slate-400 bg-slate-950 border border-slate-850 p-4.5 rounded-xl leading-relaxed">
                💡 Узнать свой ID можно, написав команду <code class="text-indigo-400 bg-indigo-950/40 px-1.5 py-0.5 rounded font-mono font-bold">/getmyid</code> боту заведения в Telegram.
              </div>
            </div>

            <!-- Modal footer -->
            <div class="px-6 py-4 border-t border-slate-800 flex justify-end gap-2 bg-slate-950/30">
              <button
                @click="closeTestModal"
                class="px-4 py-2 border border-slate-800 text-slate-400 hover:text-white rounded-xl text-sm font-semibold transition-all bg-transparent cursor-pointer"
              >
                Закрыть
              </button>
              <button
                @click="sendTestMessage"
                :disabled="sendingTest"
                class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold shadow-lg hover:shadow-indigo-500/10 transition-all active:scale-95 disabled:opacity-50 cursor-pointer flex items-center gap-2"
              >
                <span v-if="sendingTest" class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
                {{ sendingTest ? 'Отправка...' : 'Отправить тест' }}
              </button>
            </div>
          </div>
        </div>

        <!-- TAB: LLM Settings -->
        <div v-show="activeTab === 'llm'" class="bg-slate-900 rounded-2xl border border-slate-800 p-6 space-y-6">
          <div>
            <label class="form-label">Провайдер LLM</label>
            <select id="input-llm-provider" v-model="form.llm_provider" class="form-input">
              <option value="openai">OpenAI (GPT)</option>
              <option value="anthropic">Anthropic Claude</option>
              <option value="gemini">Google Gemini</option>
              <option value="deepseek">DeepSeek</option>
            </select>
          </div>
          <div>
            <label class="form-label">Модель LLM</label>
            <select v-model="selectedModelOption" class="form-input mb-3">
              <option v-for="model in availableModels" :key="model.value" :value="model.value">
                {{ model.label }}
              </option>
            </select>
            <div v-if="selectedModelOption === 'custom'" class="transition-all duration-200">
              <label class="form-label text-xs text-slate-400">Имя кастомной модели</label>
              <input id="input-llm-model" v-model="customModelName" type="text" class="form-input" placeholder="например: deepseek-coder, gpt-4o-audio" />
            </div>
          </div>
          <div>
            <label class="form-label">API Ключ</label>
            <div class="relative">
              <input id="input-llm-api-key" v-model="form.llm_api_key" :type="showLlmKey ? 'text' : 'password'" class="form-input pr-12" placeholder="Введите API ключ..." />
              <button type="button" @click="showLlmKey = !showLlmKey"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
                {{ showLlmKey ? '🙈' : '👁' }}
              </button>
            </div>
            <p class="text-[10px] text-slate-500 mt-1">Ключ хранится в зашифрованном виде. При повторном сохранении оставьте плейсхолдер ••••••••, чтобы не перезаписывать существующий ключ.</p>
          </div>
          <div>
            <label class="form-label">Системный промпт для AI-агента</label>
            <textarea id="input-llm-prompt" v-model="form.llm_system_prompt" class="form-input min-h-[120px] resize-none" placeholder="Вы — полезный AI-помощник..."></textarea>
          </div>
          <div class="flex justify-end pt-2">
            <SaveButton :saving="savingLlm" @save="saveLlmSettings" />
          </div>
        </div>
      </div>

    <!-- Preset Modal -->
    <div v-if="showPresetModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div class="bg-slate-950 border border-slate-800 rounded-3xl p-8 w-full max-w-md shadow-2xl">
        <h2 class="text-lg font-bold text-white mb-6">{{ presetModalMode === 'create' ? 'Добавить кастомный отчет' : 'Редактировать кастомный отчет' }}</h2>
        <form @submit.prevent="savePreset" class="space-y-4">
          <div>
            <label class="form-label">Название отчета</label>
            <input v-model="presetForm.name" type="text" class="form-input" placeholder="например: Отчет по списаниям" required />
          </div>
          <div>
            <label class="form-label">Описание</label>
            <textarea v-model="presetForm.description" class="form-input min-h-[60px]" placeholder="Краткое описание назначения отчета..."></textarea>
          </div>
          <div>
            <label class="form-label">UUID пресета в iiko RMS (presetId)</label>
            <input v-model="presetForm.preset_id" type="text" class="form-input font-mono text-sm" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" required />
          </div>
          <div class="flex gap-3 pt-4">
            <button type="button" @click="showPresetModal = false" class="flex-1 border border-slate-850 text-slate-400 hover:text-white py-2.5 rounded-xl text-sm font-medium transition-all">Отмена</button>
            <button type="submit" class="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white py-2.5 rounded-xl text-sm font-semibold transition-all">Сохранить</button>
          </div>
        </form>
      </div>
    </div>

    <!-- WABA Rule Modal (Mapping Constructor) -->
    <div v-if="showRuleModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div class="bg-slate-950 border border-slate-800 rounded-3xl p-6 w-full max-w-2xl shadow-2xl max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
          <h2 class="text-lg font-bold text-white flex items-center gap-2">
            <span>⚙</span>
            {{ ruleModalMode === 'create' ? 'Создать правило отправки WABA' : 'Редактировать правило отправки' }}
          </h2>
          <button @click="showRuleModal = false" class="text-slate-500 hover:text-white text-lg">✕</button>
        </div>

        <form @submit.prevent="saveRule" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="form-label">Название правила</label>
              <input v-model="ruleForm.name" type="text" class="form-input" placeholder="например: Код подтверждения" required />
            </div>
            <div>
              <label class="form-label">Событие вебхука iiko</label>
              <select v-model="ruleForm.event_type" class="form-input" required>
                <option value="auth_code">🔐 Код авторизации (проверочный код)</option>
                <option value="balance">💳 Изменение баланса кошелька</option>
                <option value="push">📢 Информационный пуш (SimplePush)</option>
                <option value="custom">⚙ Пользовательское событие</option>
              </select>
            </div>
          </div>

          <div>
            <label class="form-label">Шаблон Meta WhatsApp</label>
            <select v-model="ruleForm.template_name" @change="onTemplateSelected" class="form-input" required>
              <option value="" disabled>-- Выберите утвержденный шаблон --</option>
              <option v-if="ruleForm.template_name && !approvedTemplates.some(t => t.name === ruleForm.template_name)" :value="ruleForm.template_name">
                {{ ruleForm.template_name }} (текущий в сценарии)
              </option>
              <option v-for="t in approvedTemplates" :key="t.name + t.language" :value="t.name">
                {{ t.name }} ({{ t.language }}) - {{ t.category }}
              </option>
            </select>
            <p v-if="approvedTemplates.length === 0" class="text-[11px] text-amber-400 mt-1">
              ⚠️ Шаблоны еще не загружены. Сначала нажмите кнопку «Выгрузить шаблоны из Meta» во вкладке WABA.
            </p>
          </div>

          <!-- Template WhatsApp Preview Bubble -->
          <div v-if="selectedTemplateObj" class="bg-emerald-950/20 border border-emerald-800/40 rounded-xl p-4 space-y-2">
            <span class="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">Предпросмотр сообщения WhatsApp:</span>
            <div class="bg-[#128C7E]/20 border border-[#128C7E]/40 rounded-lg p-3 text-white text-xs space-y-1 font-sans">
              <div v-if="getTemplateHeaderText(selectedTemplateObj)" class="font-bold text-emerald-200">
                {{ getTemplateHeaderText(selectedTemplateObj) }}
              </div>
              <div class="whitespace-pre-wrap leading-relaxed text-slate-200">
                {{ getTemplateBodyText(selectedTemplateObj) }}
              </div>
              <div v-if="getTemplateButtons(selectedTemplateObj).length > 0" class="pt-2 border-t border-emerald-700/30 flex gap-2">
                <span v-for="btn in getTemplateButtons(selectedTemplateObj)" :key="btn.index" class="bg-emerald-600/30 border border-emerald-500/30 px-3 py-1 rounded text-[11px] text-emerald-300">
                  🔗 {{ btn.text }}
                </span>
              </div>
            </div>
          </div>

          <!-- Parameter Mapping Section -->
          <div v-if="selectedTemplateObj" class="border border-slate-800 rounded-xl p-4 bg-slate-900/50 space-y-4">
            <div class="flex items-center justify-between border-b border-slate-800 pb-2">
              <h3 class="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                <span>🔄</span> Подстановка параметров из вебхука iiko
              </h3>
              <span class="text-[11px] text-slate-400">Выберите, какие данные подставлять в переменные шаблона</span>
            </div>

            <!-- Header Parameters -->
            <div v-if="ruleForm.parameter_mappings.header?.length > 0" class="space-y-2">
              <span class="text-xs font-semibold text-indigo-300">Заголовок (Header):</span>
              <div v-for="h in ruleForm.parameter_mappings.header" :key="h.param" class="grid grid-cols-[100px_1fr] items-center gap-2">
                <span class="text-xs text-slate-400">Параметр {{ h.param }}:</span>
                <select v-model="h.source" class="form-input !py-1 text-xs">
                  <option v-for="opt in webhookSourceOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
              </div>
            </div>

            <!-- Body Parameters -->
            <div v-if="ruleForm.parameter_mappings.body?.length > 0" class="space-y-2">
              <span class="text-xs font-semibold text-indigo-300">Тело сообщения (Body):</span>
              <div v-for="b in ruleForm.parameter_mappings.body" :key="b.param" class="grid grid-cols-[100px_1fr] items-center gap-2">
                <span class="text-xs text-slate-400 font-mono">Переменная &#123;&#123;{{ b.param }}&#125;&#125;:</span>
                <div class="flex items-center gap-2">
                  <select v-model="b.source" class="form-input !py-1 text-xs">
                    <option v-for="opt in webhookSourceOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                  </select>
                  <input v-if="b.source === 'static'" v-model="b.static_value" type="text" class="form-input !py-1 text-xs" placeholder="Текст..." />
                </div>
              </div>
            </div>

            <!-- Button Parameters -->
            <div v-if="ruleForm.parameter_mappings.buttons?.length > 0" class="space-y-2">
              <span class="text-xs font-semibold text-indigo-300">Кнопка со ссылкой (Button URL):</span>
              <div v-for="btn in ruleForm.parameter_mappings.buttons" :key="btn.index" class="grid grid-cols-[100px_1fr] items-center gap-2">
                <span class="text-xs text-slate-400">Кнопка {{ btn.index + 1 }}:</span>
                <div class="flex items-center gap-2">
                  <select v-model="btn.source" class="form-input !py-1 text-xs">
                    <option v-for="opt in webhookSourceOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                  </select>
                  <input v-if="btn.source === 'static'" v-model="btn.static_value" type="text" class="form-input !py-1 text-xs" placeholder="Значение..." />
                </div>
              </div>
            </div>
          </div>

          <div class="flex items-center justify-between pt-4 border-t border-slate-800">
            <button type="button" @click="showRuleModal = false" class="px-4 py-2 text-xs font-medium text-slate-400 hover:text-white border border-slate-800 rounded-xl transition-all">
              Отмена
            </button>
            <button type="submit" :disabled="savingRule" class="px-5 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl transition-all flex items-center gap-2 disabled:opacity-50">
              <span v-if="savingRule" class="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              <span>Сохранить сценарий</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- WABA Quick Test Modal -->
    <div v-if="showWabaTestModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div class="bg-slate-950 border border-slate-800 rounded-3xl p-6 w-full max-w-md shadow-2xl">
        <div class="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
          <h2 class="text-base font-bold text-white flex items-center gap-2">
            <span>🧪</span> Тестовая отправка WhatsApp
          </h2>
          <button @click="showWabaTestModal = false" class="text-slate-500 hover:text-white">✕</button>
        </div>

        <form @submit.prevent="sendWabaTest" class="space-y-4">
          <div>
            <label class="form-label">Номер телефона получателя</label>
            <input v-model="wabaTestPhone" type="text" class="form-input font-mono" placeholder="+77071234567" required />
          </div>
          <div>
            <label class="form-label">Шаблон Meta</label>
            <select v-model="wabaTestTemplate" class="form-input" required>
              <option value="" disabled>-- Выберите шаблон --</option>
              <option v-for="t in approvedTemplates" :key="t.name" :value="t.name">
                {{ t.name }} ({{ t.language }})
              </option>
            </select>
          </div>

          <div class="flex gap-3 pt-2">
            <button type="button" @click="showWabaTestModal = false" class="flex-1 py-2 text-xs font-medium text-slate-400 hover:text-white border border-slate-800 rounded-xl transition-all">
              Отмена
            </button>
            <button type="submit" :disabled="sendingWabaTest" class="flex-1 py-2 text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl transition-all flex items-center justify-center gap-2 disabled:opacity-50">
              <span v-if="sendingWabaTest" class="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              <span>Отправить</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- WABA Dispatch Logs Modal (with Date Range & Excel Export) -->
    <div v-if="showWabaLogsModal" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-3 md:p-6 animate-in fade-in duration-200">
      <div class="bg-slate-950 border border-slate-800 rounded-3xl w-full max-w-6xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
        
        <!-- Modal Header -->
        <div class="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/70">
          <div>
            <h2 class="text-base md:text-lg font-bold text-white flex items-center gap-2">
              <span>📜</span> Журнал отправки сообщений WABA
            </h2>
            <p class="text-xs text-slate-400 mt-0.5">
              История отправки сообщений, коды подтверждения и уведомления через WhatsApp
            </p>
          </div>
          <button @click="showWabaLogsModal = false" class="text-slate-400 hover:text-white p-2 text-sm transition-colors rounded-lg hover:bg-slate-800 cursor-pointer">
            ✕
          </button>
        </div>

        <!-- Filter & Export Controls Bar -->
        <div class="p-4 bg-slate-900/40 border-b border-slate-800 flex flex-wrap items-end justify-between gap-3">
          <div class="flex flex-wrap items-end gap-3 flex-1 min-w-[280px]">
            <div>
              <label class="block text-[11px] font-semibold text-slate-400 mb-1">С даты:</label>
              <input type="date" v-model="wabaLogFilters.startDate" class="form-input !py-1.5 !px-2.5 text-xs font-mono bg-slate-900 text-white rounded-lg border-slate-700" />
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-slate-400 mb-1">По дату:</label>
              <input type="date" v-model="wabaLogFilters.endDate" class="form-input !py-1.5 !px-2.5 text-xs font-mono bg-slate-900 text-white rounded-lg border-slate-700" />
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-slate-400 mb-1">Статус:</label>
              <select v-model="wabaLogFilters.status" class="form-input !py-1.5 !px-2.5 text-xs bg-slate-900 text-white rounded-lg border-slate-700">
                <option value="">Все статусы</option>
                <option value="SENT">✓ Отправлено</option>
                <option value="FAILED">✕ Ошибка</option>
                <option value="PENDING">⏳ В очереди</option>
              </select>
            </div>
            <div class="flex-1 min-w-[160px]">
              <label class="block text-[11px] font-semibold text-slate-400 mb-1">Поиск:</label>
              <input type="text" v-model="wabaLogFilters.search" placeholder="Телефон, шаблон, текст..." class="form-input !py-1.5 !px-2.5 text-xs bg-slate-900 text-white rounded-lg border-slate-700" @keyup.enter="loadWabaLogsFiltered" />
            </div>
            <button @click="loadWabaLogsFiltered" :disabled="loadingWabaLogs" class="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-lg transition-all flex items-center gap-1.5 disabled:opacity-50 cursor-pointer">
              <span v-if="loadingWabaLogs" class="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              <span>🔍 Применить</span>
            </button>
            <button v-if="wabaLogFilters.startDate || wabaLogFilters.endDate || wabaLogFilters.status || wabaLogFilters.search" @click="resetWabaLogFilters" class="px-2.5 py-1.5 text-slate-400 hover:text-white text-xs transition-colors cursor-pointer">
              Сброс
            </button>
          </div>

          <!-- Export Excel Button -->
          <div>
            <button @click="exportWabaLogsExcel" :disabled="exportingWabaLogs" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl transition-all shadow-md hover:shadow-emerald-500/20 flex items-center gap-2 disabled:opacity-50 cursor-pointer">
              <span v-if="exportingWabaLogs" class="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              <span v-else>📥</span>
              <span>Выгрузить в Excel (.xlsx)</span>
            </button>
          </div>
        </div>

        <!-- Table Body (Scrollable) -->
        <div class="flex-1 overflow-y-auto p-4">
          <div v-if="loadingWabaLogs" class="py-16 flex flex-col items-center justify-center gap-2">
            <div class="w-8 h-8 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
            <span class="text-xs text-slate-400">Загрузка журнала...</span>
          </div>
          <div v-else-if="wabaLogs.length === 0" class="py-16 text-center text-slate-500">
            <span class="text-3xl block mb-2">📭</span>
            <p class="text-sm font-medium">Событий за указанный период не найдено</p>
            <p class="text-xs text-slate-600 mt-1">Попробуйте изменить параметры фильтра или сбросить даты</p>
          </div>
          <div v-else class="overflow-x-auto border border-slate-800 rounded-xl">
            <table class="w-full text-left text-xs border-collapse">
              <thead>
                <tr class="bg-slate-900 text-slate-400 border-b border-slate-800 font-semibold sticky top-0 z-10">
                  <th class="py-3 px-4">Время</th>
                  <th class="py-3 px-4">Телефон</th>
                  <th class="py-3 px-4">Событие</th>
                  <th class="py-3 px-4">Шаблон Meta</th>
                  <th class="py-3 px-4">Статус</th>
                  <th class="py-3 px-4">WABA Message ID</th>
                  <th class="py-3 px-4">Содержимое / Ошибка</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-800/70">
                <tr v-for="log in wabaLogs" :key="log.id" class="hover:bg-slate-900/50 transition-colors">
                  <td class="py-3 px-4 font-mono text-slate-400 whitespace-nowrap">{{ formatLogDate(log.created_at) }}</td>
                  <td class="py-3 px-4 font-mono font-medium text-white whitespace-nowrap">{{ log.phone }}</td>
                  <td class="py-3 px-4 whitespace-nowrap">
                    <span class="px-2 py-0.5 rounded text-[10px] font-medium"
                      :class="{
                        'bg-blue-500/10 text-blue-400 border border-blue-500/20': log.message_type === 'auth_code',
                        'bg-amber-500/10 text-amber-400 border border-amber-500/20': log.message_type === 'balance',
                        'bg-purple-500/10 text-purple-400 border border-purple-500/20': log.message_type === 'push',
                        'bg-slate-800 text-slate-300': !['auth_code','balance','push'].includes(log.message_type)
                      }">
                      {{ formatEventType(log.message_type) }}
                    </span>
                  </td>
                  <td class="py-3 px-4 text-slate-300 font-mono">{{ log.template_name }}</td>
                  <td class="py-3 px-4 whitespace-nowrap">
                    <span v-if="log.status === 'SENT'" class="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1 w-fit">
                      <span>✓</span> Отправлено
                    </span>
                    <span v-else-if="log.status === 'FAILED'" class="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center gap-1 w-fit">
                      <span>✕</span> Ошибка
                    </span>
                    <span v-else class="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center gap-1 w-fit">
                      <span>⏳</span> В очереди
                    </span>
                  </td>
                  <td class="py-3 px-4 font-mono text-[11px] text-slate-400 max-w-[140px] truncate" :title="log.waba_message_id">
                    {{ log.waba_message_id || '—' }}
                  </td>
                  <td class="py-3 px-4 text-slate-300 max-w-sm">
                    <div v-if="log.status === 'FAILED'" class="text-rose-400 font-mono text-[11px] break-words">
                      {{ log.error_message }}
                    </div>
                    <div v-else class="text-slate-300 text-[11px] break-words line-clamp-2" :title="log.rendered_text">
                      {{ log.rendered_text || '—' }}
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="p-4 bg-slate-900/60 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div>
            Показано событий: <span class="text-white font-medium">{{ wabaLogs.length }}</span>
            <span v-if="wabaLogsTotalCount"> из <span class="text-white font-medium">{{ wabaLogsTotalCount }}</span></span>
          </div>
          <button @click="showWabaLogsModal = false" class="px-4 py-2 bg-slate-800 hover:bg-slate-750 text-white rounded-xl text-xs font-semibold transition-colors cursor-pointer">
            Закрыть
          </button>
        </div>

      </div>
    </div>

    <!-- WABA Required Alert Modal -->
    <div v-if="showWabaRequiredModal" class="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div class="bg-slate-950 border border-amber-500/40 rounded-3xl p-6 w-full max-w-md shadow-2xl space-y-4">
        <div class="flex items-center gap-3">
          <span class="w-12 h-12 rounded-2xl bg-amber-500/20 text-amber-400 flex items-center justify-center text-2xl font-bold">⚠️</span>
          <div>
            <h3 class="text-white font-bold text-base">Требуется настройка WABA</h3>
            <p class="text-amber-400/90 text-xs">WhatsApp Business API не активен</p>
          </div>
        </div>
        <p class="text-slate-300 text-sm leading-relaxed">
          Включение страницы онбординга заблокировано. Для авторизации и регистрации клиентов на веб-странице система отправляет проверочный код через WhatsApp.
        </p>
        <p class="text-slate-400 text-xs">
          Пожалуйста, перейдите в раздел <b>Настройка WABA</b>, укажите Meta Access Token, Phone Number ID и включите тумблер WABA.
        </p>
        <div class="flex gap-3 pt-2">
          <button @click="showWabaRequiredModal = false" type="button" class="flex-1 py-2.5 rounded-xl border border-slate-700 text-slate-300 hover:text-white text-xs font-medium transition-all cursor-pointer">
            Понятно
          </button>
          <button @click="showWabaRequiredModal = false; activeTab = 'waba'" type="button" class="flex-1 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold shadow-md transition-all cursor-pointer">
            Настроить WABA →
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import QRCode from 'qrcode'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import SaveButton from '@/components/SaveButton.vue'

const auth = useAuthStore()
const toast = useToastStore()
const route = useRoute()
const router = useRouter()

const tabs = computed(() => {
  const list = [
    { id: 'general', label: 'Основные / Telegram' },
    { id: 'waba', label: 'Настройка WABA' },
    { id: 'iiko', label: 'Интеграция iiko Cloud API' },
    { id: 'iiko_server', label: 'Интеграция iiko Server API' },
  ]
  if (form.value.is_loyalty_enabled) {
    list.push(
      { id: 'card_tiers', label: 'Ранги и дизайн карт' },
      { id: 'onboarding', label: 'Страница онбординга' },
      { id: 'branding', label: 'Брендинг TMA' },
      { id: 'wallet', label: 'Google Wallet' },
      { id: 'apple_wallet', label: 'Apple Wallet' },
      { id: 'loyalty_programs', label: 'Программа лояльности' }
    )
  }
  if (form.value.is_ai_agent_enabled) {
    list.push({ id: 'llm', label: 'Настройки LLM' })
  }
  return list
})

const activeTab = ref(route.query.tab ? String(route.query.tab) : 'general')

const currentTabLabel = computed(() => {
  const t = tabs.value.find(tab => tab.id === activeTab.value)
  return t ? `Раздел: ${t.label}` : 'Управление конфигурацией ресторана'
})

watch(() => route.query.tab, (newTab) => {
  activeTab.value = newTab ? String(newTab) : 'general'
}, { immediate: true })
const loading = ref(true)
const saving = ref(false)
const uploadingLogo = ref(false)
const showToken = ref(false)
const logoPreview = ref(null)

const checkingWebhook = ref(false)
const registeringWebhook = ref(false)
const webhookStatus = ref(null)

const webhookUrl = computed(() => {
  const domain = import.meta.env.VITE_WEBHOOK_DOMAIN || window.location.origin
  const cleanDomain = domain.replace(/\/$/, '')
  return `${cleanDomain}/api/v1/integrations/iiko/webhook/`
})

async function copyWebhookUrl() {
  try {
    await navigator.clipboard.writeText(webhookUrl.value)
    toast.success('Ссылка скопирована')
  } catch {
    toast.error('Не удалось скопировать')
  }
}

async function checkWebhookStatus() {
  if (!form.value.tg_bot_token) {
    toast.error('Сначала укажите и сохраните токен бота')
    return
  }
  checkingWebhook.value = true
  try {
    const res = await api.get(`/core/organizations/${auth.currentOrgId}/webhook-status/`)
    webhookStatus.value = res.data
    toast.success('Статус вебхука обновлен')
  } catch (e) {
    toast.error(e.response?.data?.error || 'Ошибка проверки статуса вебхука')
    webhookStatus.value = null
  } finally {
    checkingWebhook.value = false
  }
}

async function registerWebhook() {
  if (!form.value.tg_bot_token) {
    toast.error('Сначала укажите и сохраните токен бота')
    return
  }
  registeringWebhook.value = true
  try {
    await api.post(`/core/organizations/${auth.currentOrgId}/webhook-status/`)
    toast.success('Вебхук успешно установлен в Telegram')
    await checkWebhookStatus()
  } catch (e) {
    toast.error(e.response?.data?.error || 'Ошибка установки вебхука')
  } finally {
    registeringWebhook.value = false
  }
}

// Test message states & methods
const testModalOpen = ref(false)
const testTelegramId = ref('')
const sendingTest = ref(false)

function openTestModal() {
  testTelegramId.value = auth.user?.telegram_id || ''
  testModalOpen.value = true
}

function closeTestModal() {
  testModalOpen.value = false
}

async function sendTestMessage() {
  if (!testTelegramId.value.trim()) return toast.error('Укажите Telegram ID')
  sendingTest.value = true
  try {
    await api.post(`/core/organizations/${auth.currentOrgId}/send-test-message/`, {
      telegram_id: testTelegramId.value.trim()
    })
    toast.success('Тестовое сообщение успешно отправлено')
    if (auth.user) {
      auth.user.telegram_id = testTelegramId.value.trim()
    }
    closeTestModal()
  } catch (e) {
    toast.error(e.response?.data?.error || 'Не удалось отправить тестовое сообщение')
  } finally {
    sendingTest.value = false
  }
}

const syncingWallet = ref(false)
const uploadingWalletLogo = ref(false)
const walletLogoPreview = ref(null)
const uploadingBanner = ref(false)
const bannerPreview = ref(null)
const walletForm = ref({
  issuer_id: '',
  class_name: '',
  issuer_name: '',
  logo_url: '',
  hero_image_url: '',
  hex_background_color: '#000000',
  locations: [],
  push_templates: {
    ru: {
      title: 'Баланс бонусов обновлен',
      body: '{org_name}: начислено +{change} бонусов! Баланс: {balance} б.'
    },
    kz: {
      title: 'Бонус балансы жаңартылды',
      body: '{org_name}: +{change} бонус берілді! Балансыңыз: {balance} балл.'
    }
  }
})

const showWalletAdvancedModal = ref(false)
const activeWalletModalTab = ref('geo')
const activePushLang = ref('ru')
const newLocation = ref({
  name: '',
  latitude: '',
  longitude: ''
})

const savingAppleWallet = ref(false)
const uploadingAppleLogo = ref(false)
const appleLogoPreview = ref(null)
const uploadingAppleStrip = ref(false)
const appleStripPreview = ref(null)
const appleWalletForm = ref({
  pass_type_id: '',
  team_id: '',
  class_name: '',
  logo_url: '',
  strip_url: '',
  barcode_type: 'barcode',
  background_color: '#18181b',
  foreground_color: '#ffffff',
  label_color: '#94a3b8',
  locations: [],
  push_templates: {
    ru: {
      change_message: 'Баланс бонусов обновлен: %@ баллов',
      welcome_geo_text: 'Добро пожаловать! Предъявите карту для бонусов.'
    },
    kz: {
      change_message: 'Бонус балансы жаңартылды: %@ балл',
      welcome_geo_text: 'Қош келдіңіз! Бонустарды алу үшін картаңызды көрсетіңіз.'
    }
  }
})

const showAppleAdvancedModal = ref(false)
const activeAppleModalTab = ref('geo')
const activeApplePushLang = ref('ru')
const newAppleLocation = ref({
  name: '',
  latitude: '',
  longitude: '',
  relevant_text: ''
})

const form = ref({
  name: '', slug: '', address: '',
  tg_bot_token: '', tg_bot_username: '', tma_name: '', tma_direct_link: '',
  is_google_wallet_enabled: false,
  is_apple_wallet_enabled: false,
  apple_pass_type_id: '',
  apple_team_id: '',
  is_waba_enabled: false,
  waba_access_token: '',
  waba_business_account_id: '',
  waba_phone_number_id: '',
  iiko_integration_type: 'iiko_transport',
  iiko_api_base_url: 'https://api-ru.iiko.services/api/1',
  iiko_api_login: '', iiko_app_id: '', iiko_client_secret: '', iiko_organization_id: '', iiko_loyalty_program_id: '',
  is_iiko_webhook_password_enabled: false, iiko_webhook_password: '',
  iiko_server_url: '', iiko_server_login: '', iiko_server_password: '',
  is_web_onboarding_enabled: false,
  web_onboarding_settings: {},
  is_client_classification_enabled: false,
  client_classification_settings: {
    brand_color: '#6366f1',
    tiers: []
  },
  branding: {},
  instagram_link: '', whatsapp_link: '',
  is_loyalty_enabled: true, is_analytics_enabled: false, is_ai_agent_enabled: false,
  llm_provider: 'openai', llm_model_name: 'gpt-4o-mini', llm_api_key: '', llm_system_prompt: '',
})

// Onboarding page reactive state & WABA guard
const isWabaConfigured = computed(() => {
  return !!(form.value.is_waba_enabled && form.value.waba_access_token && form.value.waba_phone_number_id)
})
const showWabaRequiredModal = ref(false)

function toggleWebOnboarding() {
  if (!form.value.is_web_onboarding_enabled) {
    if (!isWabaConfigured.value) {
      showWabaRequiredModal.value = true
      toast.error('Для включения страницы онбординга необходимо сначала настроить и включить WABA!')
      return
    }
    form.value.is_web_onboarding_enabled = true
  } else {
    form.value.is_web_onboarding_enabled = false
  }
}

const onboardingAccentColor = computed({
  get: () => form.value.web_onboarding_settings?.accent_color || form.value.branding?.design_color || '#6366f1',
  set: (v) => {
    form.value.web_onboarding_settings = {
      ...(form.value.web_onboarding_settings || {}),
      accent_color: v
    }
  }
})

const onboardingTitleKz = computed({
  get: () => form.value.web_onboarding_settings?.title_kz ?? 'Лоялдық картасын алыңыз',
  set: (v) => {
    form.value.web_onboarding_settings = {
      ...(form.value.web_onboarding_settings || {}),
      title_kz: v
    }
  }
})

const onboardingTitleRu = computed({
  get: () => form.value.web_onboarding_settings?.title_ru ?? 'Получите карту лояльности',
  set: (v) => {
    form.value.web_onboarding_settings = {
      ...(form.value.web_onboarding_settings || {}),
      title_ru: v
    }
  }
})

const onboardingSubtitleKz = computed({
  get: () => form.value.web_onboarding_settings?.subtitle_kz ?? 'Тіркеліп, әрбір тапсырыстан бонустар жинаңыз!',
  set: (v) => {
    form.value.web_onboarding_settings = {
      ...(form.value.web_onboarding_settings || {}),
      subtitle_kz: v
    }
  }
})

const onboardingSubtitleRu = computed({
  get: () => form.value.web_onboarding_settings?.subtitle_ru ?? 'Зарегистрируйтесь и получайте бонусы с каждого заказа!',
  set: (v) => {
    form.value.web_onboarding_settings = {
      ...(form.value.web_onboarding_settings || {}),
      subtitle_ru: v
    }
  }
})

const onboardingWelcomeBonusKz = computed({
  get: () => form.value.web_onboarding_settings?.welcome_bonus_kz || '',
  set: (v) => {
    form.value.web_onboarding_settings = {
      ...(form.value.web_onboarding_settings || {}),
      welcome_bonus_kz: v
    }
  }
})

const onboardingWelcomeBonusRu = computed({
  get: () => form.value.web_onboarding_settings?.welcome_bonus_ru || '',
  set: (v) => {
    form.value.web_onboarding_settings = {
      ...(form.value.web_onboarding_settings || {}),
      welcome_bonus_ru: v
    }
  }
})

const onboardingUrl = computed(() => {
  const domain = window.location.origin
  return `${domain}/join/${form.value.slug || ''}`
})

const qrCodeDataUrl = ref('')
async function generateQrCode() {
  if (!form.value.slug) return
  try {
    qrCodeDataUrl.value = await QRCode.toDataURL(onboardingUrl.value, {
      width: 400,
      margin: 2,
      color: {
        dark: '#0f172a',
        light: '#ffffff'
      }
    })
  } catch (e) {
    console.error('Failed to generate QR code', e)
  }
}

watch([onboardingUrl, () => activeTab.value], () => {
  if (activeTab.value === 'onboarding') {
    generateQrCode()
  }
}, { immediate: true })

async function copyOnboardingUrl() {
  try {
    await navigator.clipboard.writeText(onboardingUrl.value)
    toast.success('Ссылка на страницу онбординга скопирована')
  } catch {
    toast.error('Не удалось скопировать ссылку')
  }
}

function downloadQrCode() {
  if (!qrCodeDataUrl.value) return
  const link = document.createElement('a')
  link.download = `qr-onboarding-${form.value.slug}.png`
  link.href = qrCodeDataUrl.value
  link.click()
  toast.success('QR-код скачан')
}

const uploadingOnboardingBanner = ref(false)
const onboardingBannerPreview = ref(null)

async function uploadOnboardingBanner(event) {
  const file = event.target.files?.[0]
  if (!file) return
  onboardingBannerPreview.value = URL.createObjectURL(file)
  uploadingOnboardingBanner.value = true
  try {
    const fd = new FormData()
    fd.append('banner', file)
    const res = await api.post(`/core/organizations/${auth.currentOrgId}/upload-onboarding-banner/`, fd)
    form.value.web_onboarding_settings = {
      ...(form.value.web_onboarding_settings || {}),
      banner_url: res.data.banner_url
    }
    toast.success('Баннер страницы онбординга загружен')
  } catch {
    toast.error('Ошибка загрузки баннера')
    onboardingBannerPreview.value = null
  } finally {
    uploadingOnboardingBanner.value = false
  }
}

async function saveOnboardingSettings() {
  if (form.value.is_web_onboarding_enabled && !isWabaConfigured.value) {
    showWabaRequiredModal.value = true
    toast.error('Для включения страницы онбординга необходимо сначала настроить и включить WABA!')
    form.value.is_web_onboarding_enabled = false
    return
  }
  saving.value = true
  try {
    await api.patch(`/core/organizations/${auth.currentOrgId}/settings/`, {
      is_web_onboarding_enabled: form.value.is_web_onboarding_enabled,
      web_onboarding_settings: form.value.web_onboarding_settings,
    })
    toast.success('Настройки страницы онбординга сохранены')
  } catch (e) {
    const msg = e.response?.data?.is_web_onboarding_enabled?.[0] || e.response?.data?.detail || 'Ошибка сохранения настроек онбординга'
    toast.error(msg)
  } finally {
    saving.value = false
  }
}

// Card Tiers & Unified Brand Color logic
const quickPalette = [
  '#6366f1', '#4f46e5', '#0ea5e9', '#10b981', '#f59e0b',
  '#f97316', '#ef4444', '#ec4899', '#8b5cf6', '#1e293b', '#000000'
]

const tierColorPresets = [
  { id: 'bronze', name: 'Бронза', color: '#b45309', gradient: 'linear-gradient(135deg, #78350f, #b45309, #d97706)' },
  { id: 'silver', name: 'Серебро', color: '#64748b', gradient: 'linear-gradient(135deg, #334155, #64748b, #94a3b8)' },
  { id: 'gold', name: 'Золото', color: '#d97706', gradient: 'linear-gradient(135deg, #92400e, #d97706, #fbbf24)' },
  { id: 'platinum', name: 'Платина', color: '#475569', gradient: 'linear-gradient(135deg, #1e293b, #475569, #cbd5e1)' },
  { id: 'emerald', name: 'Изумруд', color: '#059669', gradient: 'linear-gradient(135deg, #064e3b, #059669, #34d399)' },
  { id: 'sapphire', name: 'Сапфир', color: '#2563eb', gradient: 'linear-gradient(135deg, #1e3a8a, #2563eb, #60a5fa)' },
  { id: 'ruby', name: 'Рубин', color: '#dc2626', gradient: 'linear-gradient(135deg, #881337, #e11d48, #f43f5e)' },
  { id: 'black_vip', name: 'Black VIP', color: '#09090b', gradient: 'linear-gradient(135deg, #09090b, #18181b, #27272a)' },
]

const availableIikoWallets = ref([])
const loadingIikoWallets = ref(false)
const previewTierId = ref('base')
const previewFlipped = ref(false)

const brandColor = computed({
  get: () => form.value.client_classification_settings?.brand_color || form.value.branding?.design_color || form.value.web_onboarding_settings?.accent_color || '#6366f1',
  set: (v) => {
    form.value.client_classification_settings = {
      ...(form.value.client_classification_settings || {}),
      brand_color: v
    }
    form.value.branding = {
      ...(form.value.branding || {}),
      design_color: v
    }
    form.value.web_onboarding_settings = {
      ...(form.value.web_onboarding_settings || {}),
      accent_color: v
    }
    if (walletForm.value) {
      walletForm.value.hex_background_color = v
    }
  },
})

async function fetchIikoWallets() {
  if (!auth.currentOrgId) return
  loadingIikoWallets.value = true
  try {
    const res = await api.get('/loyalty/organizations/iiko-wallets/')
    availableIikoWallets.value = res.data?.wallets || []
  } catch (e) {
    console.warn('Could not fetch iiko wallets:', e)
  } finally {
    loadingIikoWallets.value = false
  }
}

function addTier() {
  if (!form.value.client_classification_settings) {
    form.value.client_classification_settings = { brand_color: brandColor.value, tiers: [] }
  }
  if (!Array.isArray(form.value.client_classification_settings.tiers)) {
    form.value.client_classification_settings.tiers = []
  }
  const newId = 'tier_' + Date.now()
  const nextNum = form.value.client_classification_settings.tiers.length + 1
  const defaultPreset = tierColorPresets[Math.min(nextNum - 1, tierColorPresets.length - 1)] || tierColorPresets[0]
  const newTier = {
    id: newId,
    name: `Уровень ${nextNum}`,
    name_kz: `Деңгей ${nextNum}`,
    badge: `Tier ${nextNum}`,
    color: defaultPreset.color,
    gradient: defaultPreset.gradient,
    gradient_preset: defaultPreset.id,
    cashback_percent: nextNum * 5,
    iiko_wallet_name: '',
    keywords: '',
    banner_url: '',
  }
  form.value.client_classification_settings.tiers.push(newTier)
  previewTierId.value = newId
}

function removeTier(index) {
  const removed = form.value.client_classification_settings?.tiers?.splice(index, 1)?.[0]
  if (previewTierId.value === removed?.id) {
    previewTierId.value = form.value.client_classification_settings?.tiers?.[0]?.id || 'base'
  }
}

function addDefaultTiers() {
  if (!form.value.client_classification_settings) {
    form.value.client_classification_settings = { brand_color: brandColor.value, tiers: [] }
  }
  form.value.client_classification_settings.tiers = [
    {
      id: 'tier_silver',
      name: 'Silver',
      name_kz: 'Silver',
      badge: 'Silver Pass',
      color: '#64748b',
      gradient: 'linear-gradient(135deg, #334155, #64748b, #94a3b8)',
      gradient_preset: 'silver',
      cashback_percent: 5,
      iiko_wallet_name: '',
      keywords: 'silver, серебр, 5%',
    },
    {
      id: 'tier_gold',
      name: 'Gold',
      name_kz: 'Gold',
      badge: 'Gold VIP',
      color: '#d97706',
      gradient: 'linear-gradient(135deg, #92400e, #d97706, #fbbf24)',
      gradient_preset: 'gold',
      cashback_percent: 10,
      iiko_wallet_name: '',
      keywords: 'gold, золот, 10%',
    },
    {
      id: 'tier_vip',
      name: 'Platinum VIP',
      name_kz: 'Platinum VIP',
      badge: 'Black VIP',
      color: '#09090b',
      gradient: 'linear-gradient(135deg, #09090b, #18181b, #27272a)',
      gradient_preset: 'black_vip',
      cashback_percent: 15,
      iiko_wallet_name: '',
      keywords: 'vip, вип, платин, 15%',
    },
  ]
  previewTierId.value = 'tier_gold'
}

function applyPresetToTier(tier, preset) {
  tier.gradient_preset = preset.id
  tier.gradient = preset.gradient
  tier.color = preset.color
}

const uploadingTierBannerId = ref(null)

async function uploadTierBanner(tier, event) {
  const file = event.target.files?.[0]
  if (!file) return

  uploadingTierBannerId.value = tier.id
  try {
    const fd = new FormData()
    fd.append('image', file)
    const res = await api.post(`/core/organizations/${auth.currentOrgId}/upload-tier-banner/`, fd)
    if (res.data?.banner_url) {
      tier.banner_url = res.data.banner_url
    }
  } catch (err) {
    console.error('Failed to upload tier banner:', err)
  } finally {
    uploadingTierBannerId.value = null
    event.target.value = ''
  }
}

const activePreviewTier = computed(() => {
  if (previewTierId.value === 'base') return null
  const tiers = form.value.client_classification_settings?.tiers || []
  return tiers.find(t => t.id === previewTierId.value) || tiers[0] || null
})

const previewCardStyle = computed(() => {
  if (activePreviewTier.value) {
    if (activePreviewTier.value.banner_url) {
      return {
        background: `linear-gradient(rgba(0, 0, 0, 0.35), rgba(0, 0, 0, 0.75)), url(${activePreviewTier.value.banner_url}) center/cover no-repeat`
      }
    }
    if (activePreviewTier.value.gradient) {
      return { background: activePreviewTier.value.gradient }
    }
    const c = activePreviewTier.value.color || brandColor.value
    return { background: `linear-gradient(135deg, ${c}, #000000)` }
  }
  const base = brandColor.value || '#6366f1'
  return { background: `linear-gradient(135deg, ${base}, #0f172a)` }
})
const greetingText = computed({
  get: () => form.value.branding?.greeting_text || '',
  set: (v) => { form.value.branding = { ...form.value.branding, greeting_text: v } },
})
const greetingTextKz = computed({
  get: () => form.value.branding?.greeting_text_kz || '',
  set: (v) => { form.value.branding = { ...form.value.branding, greeting_text_kz: v } },
})

const showLlmKey = ref(false)

const providerModels = {
  openai: [
    { value: 'gpt-4o-mini', label: 'GPT-4o Mini (Быстрая, Рекомендуемая)' },
    { value: 'gpt-4o', label: 'GPT-4o (Максимальная точность)' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' }
  ],
  anthropic: [
    { value: 'claude-3-5-sonnet-20240620', label: 'Claude 3.5 Sonnet (Интеллектуальная)' },
    { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku (Экономичная)' },
    { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus' }
  ],
  gemini: [
    { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash (Быстрая)' },
    { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro (Продвинутая)' },
    { value: 'gemini-1.0-pro', label: 'Gemini 1.0 Pro' }
  ],
  deepseek: [
    { value: 'deepseek-chat', label: 'DeepSeek Chat (DeepSeek-V3)' },
    { value: 'deepseek-reasoner', label: 'DeepSeek Reasoner (DeepSeek-R1, Рассуждения)' }
  ]
}

const selectedModelOption = ref('gpt-4o-mini')
const customModelName = ref('')

const availableModels = computed(() => {
  const provider = form.value.llm_provider
  const models = providerModels[provider] || []
  return [...models, { value: 'custom', label: 'Ввести имя модели вручную...' }]
})

watch(() => form.value.llm_provider, (newProvider) => {
  const models = providerModels[newProvider] || []
  if (models.length > 0) {
    selectedModelOption.value = models[0].value
    form.value.llm_model_name = models[0].value
  } else {
    selectedModelOption.value = 'custom'
    customModelName.value = ''
    form.value.llm_model_name = ''
  }
})

watch(selectedModelOption, (newVal) => {
  if (newVal !== 'custom') {
    form.value.llm_model_name = newVal
  } else {
    form.value.llm_model_name = customModelName.value
  }
})

watch(customModelName, (newVal) => {
  if (selectedModelOption.value === 'custom') {
    form.value.llm_model_name = newVal
  }
})

function initLlmModelFields() {
  const provider = form.value.llm_provider
  const models = providerModels[provider] || []
  const found = models.find(m => m.value === form.value.llm_model_name)
  if (found) {
    selectedModelOption.value = form.value.llm_model_name
  } else {
    selectedModelOption.value = 'custom'
    customModelName.value = form.value.llm_model_name
  }
}

const presets = ref([])
const showPresetModal = ref(false)
const presetModalMode = ref('create')
const presetForm = ref({
  id: null,
  name: '',
  description: '',
  preset_id: ''
})

async function loadPresets() {
  try {
    const res = await api.get(`/analytics/organizations/${auth.currentOrgId}/presets/`)
    presets.value = res.data
  } catch {
    toast.error('Не удалось загрузить пресеты отчетов')
  }
}

function openCreatePresetModal() {
  presetModalMode.value = 'create'
  presetForm.value = { id: null, name: '', description: '', preset_id: '' }
  showPresetModal.value = true
}

function openEditPresetModal(preset) {
  presetModalMode.value = 'edit'
  presetForm.value = { ...preset }
  showPresetModal.value = true
}

async function savePreset() {
  try {
    const orgId = auth.currentOrgId
    if (presetModalMode.value === 'create') {
      await api.post(`/analytics/organizations/${orgId}/presets/`, {
        name: presetForm.value.name,
        description: presetForm.value.description,
        preset_id: presetForm.value.preset_id
      })
      toast.success('Кастомный отчет добавлен')
    } else {
      await api.put(`/analytics/organizations/${orgId}/presets/${presetForm.value.id}/`, {
        preset_id: presetForm.value.preset_id,
        name: presetForm.value.name,
        description: presetForm.value.description
      })
      toast.success('Кастомный отчет обновлен')
    }
    showPresetModal.value = false
    await loadPresets()
  } catch (e) {
    toast.error('Ошибка сохранения отчета')
  }
}

async function deletePreset(preset) {
  if (!confirm(`Вы действительно хотите удалить кастомный отчет "${preset.name}"?`)) return
  try {
    await api.delete(`/analytics/organizations/${auth.currentOrgId}/presets/${preset.id}/`)
    toast.success('Отчет удален')
    await loadPresets()
  } catch {
    toast.error('Не удалось удалить отчет')
  }
}

async function saveSystemPreset(preset) {
  try {
    await api.put(`/analytics/organizations/${auth.currentOrgId}/presets/${preset.id}/`, {
      preset_id: preset.preset_id,
      name: preset.name,
      description: preset.description
    })
    toast.success('Системный отчет сохранен')
    await loadPresets()
  } catch {
    toast.error('Ошибка сохранения системного отчета')
  }
}

async function load() {
  try {
    const res = await api.get(`/core/organizations/${auth.currentOrgId}/settings/`)
    form.value = { ...form.value, ...res.data }
    
    const gwSettings = res.data.google_wallet_settings || {}
    walletForm.value = {
      issuer_id: gwSettings.issuer_id || res.data.google_issuer_id || '',
      class_name: gwSettings.class_name || res.data.name || '',
      issuer_name: gwSettings.issuer_name || res.data.name || '',
      logo_url: gwSettings.logo_url || (res.data.branding?.logo_url ? (res.data.branding.logo_url.startsWith('http') ? res.data.branding.logo_url : window.location.origin + res.data.branding.logo_url) : ''),
      hero_image_url: gwSettings.hero_image_url || '',
      hex_background_color: gwSettings.hex_background_color || (res.data.branding?.design_color || '#1e1b4b'),
      locations: Array.isArray(gwSettings.locations) ? JSON.parse(JSON.stringify(gwSettings.locations)) : [],
      push_templates: gwSettings.push_templates ? JSON.parse(JSON.stringify(gwSettings.push_templates)) : {
        ru: {
          title: 'Баланс бонусов обновлен',
          body: '{org_name}: начислено +{change} бонусов! Баланс: {balance} б.'
        },
        kz: {
          title: 'Бонус балансы жаңартылды',
          body: '{org_name}: +{change} бонус берілді! Балансыңыз: {balance} балл.'
        }
      }
    }
    if (walletForm.value.logo_url) {
      walletLogoPreview.value = walletForm.value.logo_url.startsWith('http') 
        ? walletForm.value.logo_url 
        : window.location.origin + walletForm.value.logo_url
    }
    if (walletForm.value.hero_image_url) {
      bannerPreview.value = walletForm.value.hero_image_url.startsWith('http') 
        ? walletForm.value.hero_image_url 
        : window.location.origin + walletForm.value.hero_image_url
    }

    const awSettings = res.data.apple_wallet_settings || {}
    appleWalletForm.value = {
      pass_type_id: res.data.apple_pass_type_id || awSettings.pass_type_id || '',
      team_id: res.data.apple_team_id || awSettings.team_id || '',
      class_name: awSettings.class_name || res.data.name || '',
      logo_url: awSettings.logo_url || (res.data.branding?.logo_url ? (res.data.branding.logo_url.startsWith('http') ? res.data.branding.logo_url : window.location.origin + res.data.branding.logo_url) : ''),
      strip_url: awSettings.strip_url || '',
      barcode_type: awSettings.barcode_type || 'barcode',
      background_color: awSettings.background_color || (res.data.branding?.design_color || '#18181b'),
      foreground_color: awSettings.foreground_color || '#ffffff',
      label_color: awSettings.label_color || '#94a3b8',
      locations: Array.isArray(awSettings.locations) ? JSON.parse(JSON.stringify(awSettings.locations)) : [],
      push_templates: awSettings.push_templates ? JSON.parse(JSON.stringify(awSettings.push_templates)) : {
        ru: {
          change_message: 'Баланс бонусов обновлен: %@ баллов',
          welcome_geo_text: 'Добро пожаловать! Предъявите карту для бонусов.'
        },
        kz: {
          change_message: 'Бонус балансы жаңартылды: %@ балл',
          welcome_geo_text: 'Қош келдіңіз! Бонустарды алу үшін картаңызды көрсетіңіз.'
        }
      }
    }
    if (appleWalletForm.value.logo_url) {
      appleLogoPreview.value = appleWalletForm.value.logo_url.startsWith('http') 
        ? appleWalletForm.value.logo_url 
        : window.location.origin + appleWalletForm.value.logo_url
    }
    if (appleWalletForm.value.strip_url) {
      appleStripPreview.value = appleWalletForm.value.strip_url.startsWith('http') 
        ? appleWalletForm.value.strip_url 
        : window.location.origin + appleWalletForm.value.strip_url
    }
    
    initLlmModelFields()
    
    if (!form.value.client_classification_settings) {
      form.value.client_classification_settings = {
        brand_color: form.value.brand_color || form.value.branding?.design_color || '#6366f1',
        tiers: []
      }
    } else if (!form.value.client_classification_settings.brand_color) {
      form.value.client_classification_settings.brand_color = form.value.brand_color || form.value.branding?.design_color || '#6366f1'
    }
    await fetchIikoWallets()

    if (form.value.is_analytics_enabled) {
      await loadPresets()
    }
    if (activeTab.value === 'waba') {
      await loadWabaData()
    } else if (activeTab.value === 'loyalty_programs') {
      await fetchPrograms()
    }

    auth.updateOrganization({
      name: form.value.name,
      is_loyalty_enabled: form.value.is_loyalty_enabled,
      is_analytics_enabled: form.value.is_analytics_enabled,
      is_ai_agent_enabled: form.value.is_ai_agent_enabled,
    })
  } catch {
    toast.error('Не удалось загрузить настройки')
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  try {
    await api.patch(`/core/organizations/${auth.currentOrgId}/settings/`, {
      name: form.value.name,
      address: form.value.address,
      tg_bot_token: form.value.tg_bot_token || undefined,
      tg_bot_username: form.value.tg_bot_username,
      tma_name: form.value.tma_name,
      tma_direct_link: form.value.tma_direct_link || null,
      is_google_wallet_enabled: form.value.is_google_wallet_enabled,
      google_issuer_id: walletForm.value.issuer_id || null,
      google_wallet_settings: {
        issuer_id: walletForm.value.issuer_id,
        class_name: walletForm.value.class_name,
        issuer_name: walletForm.value.issuer_name,
        logo_url: walletForm.value.logo_url,
        hero_image_url: walletForm.value.hero_image_url,
        hex_background_color: walletForm.value.hex_background_color,
        locations: walletForm.value.locations || [],
        push_templates: walletForm.value.push_templates || {},
      },
      is_waba_enabled: form.value.is_waba_enabled,
      waba_access_token: form.value.waba_access_token || undefined,
      waba_business_account_id: form.value.waba_business_account_id || null,
      waba_phone_number_id: form.value.waba_phone_number_id || null,
      iiko_integration_type: form.value.iiko_integration_type,
      iiko_api_base_url: form.value.iiko_api_base_url,
      iiko_api_login: form.value.iiko_api_login || undefined,
      iiko_app_id: form.value.iiko_app_id || undefined,
      iiko_client_secret: form.value.iiko_client_secret || undefined,
      iiko_organization_id: form.value.iiko_organization_id || null,
      iiko_loyalty_program_id: form.value.iiko_loyalty_program_id || null,
      is_iiko_webhook_password_enabled: form.value.is_iiko_webhook_password_enabled,
      iiko_webhook_password: form.value.iiko_webhook_password || null,
      iiko_server_url: form.value.iiko_server_url || null,
      iiko_server_login: form.value.iiko_server_login || undefined,
      iiko_server_password: form.value.iiko_server_password || undefined,
      instagram_link: form.value.instagram_link || null,
      whatsapp_link: form.value.whatsapp_link || null,
      is_web_onboarding_enabled: form.value.is_web_onboarding_enabled,
      web_onboarding_settings: form.value.web_onboarding_settings,
      is_client_classification_enabled: form.value.is_client_classification_enabled,
      client_classification_settings: form.value.client_classification_settings,
      brand_color: brandColor.value,
      branding: form.value.branding,
    })
    auth.updateOrganization({
      name: form.value.name,
      is_loyalty_enabled: form.value.is_loyalty_enabled,
      is_analytics_enabled: form.value.is_analytics_enabled,
      is_ai_agent_enabled: form.value.is_ai_agent_enabled,
    })
    toast.success('Настройки сохранены')
  } catch (e) {
    const msg = Object.values(e.response?.data || {}).flat().join(', ') || 'Ошибка сохранения'
    toast.error(msg)
  } finally {
    saving.value = false
  }
}

const savingLlm = ref(false)

async function saveLlmSettings() {
  savingLlm.value = true
  try {
    await api.patch(`/core/organizations/${auth.currentOrgId}/settings/`, {
      llm_provider: form.value.llm_provider,
      llm_model_name: form.value.llm_model_name,
      llm_api_key: form.value.llm_api_key || undefined,
      llm_system_prompt: form.value.llm_system_prompt,
    })
    toast.success('Настройки LLM сохранены')
  } catch (e) {
    const msg = Object.values(e.response?.data || {}).flat().join(', ') || 'Ошибка сохранения настроек LLM'
    toast.error(msg)
  } finally {
    savingLlm.value = false
  }
}

const testingIiko = ref(false)

async function testIikoConnection() {
  testingIiko.value = true
  try {
    const res = await api.post(`/core/organizations/${auth.currentOrgId}/test-iiko-connection/`, {
      iiko_api_base_url: form.value.iiko_api_base_url,
      iiko_api_login: form.value.iiko_api_login,
      iiko_app_id: form.value.iiko_app_id,
      iiko_client_secret: form.value.iiko_client_secret,
    })
    toast.success(res.data.message || 'Подключение к iiko успешно установлено!')
  } catch (e) {
    const msg = e.response?.data?.error || 'Ошибка проверки подключения к iiko'
    toast.error(msg)
  } finally {
    testingIiko.value = false
  }
}

const testingIikoServer = ref(false)

async function testIikoServerConnection() {
  testingIikoServer.value = true
  try {
    const res = await api.post(`/core/organizations/${auth.currentOrgId}/test-iiko-server-connection/`, {
      iiko_server_url: form.value.iiko_server_url,
      iiko_server_login: form.value.iiko_server_login,
      iiko_server_password: form.value.iiko_server_password,
    })
    toast.success(res.data.message || 'Подключение к iiko Server успешно установлено!')
  } catch (e) {
    const msg = e.response?.data?.error || 'Ошибка проверки подключения к iiko Server'
    toast.error(msg)
  } finally {
    testingIikoServer.value = false
  }
}

async function saveBranding() {
  saving.value = true
  try {
    await api.patch(`/core/organizations/${auth.currentOrgId}/settings/`, {
      branding: form.value.branding,
    })
    toast.success('Брендинг сохранён')
  } catch {
    toast.error('Ошибка сохранения брендинга')
  } finally {
    saving.value = false
  }
}

async function uploadLogo(event) {
  const file = event.target.files?.[0]
  if (!file) return
  logoPreview.value = URL.createObjectURL(file)
  uploadingLogo.value = true
  try {
    const fd = new FormData()
    fd.append('logo', file)
    const res = await api.post(`/core/organizations/${auth.currentOrgId}/upload-logo/`, fd)
    form.value.branding = { ...form.value.branding, logo_url: res.data.logo_url }
    toast.success('Логотип загружен')
  } catch {
    toast.error('Ошибка загрузки логотипа')
    logoPreview.value = null
  } finally {
    uploadingLogo.value = false
  }
}

async function toggleGoogleWallet() {
  try {
    await api.patch(`/core/organizations/${auth.currentOrgId}/settings/`, {
      is_google_wallet_enabled: form.value.is_google_wallet_enabled
    })
    toast.success(form.value.is_google_wallet_enabled ? 'Google Wallet включен в TMA' : 'Google Wallet отключен в TMA')
  } catch (e) {
    form.value.is_google_wallet_enabled = !form.value.is_google_wallet_enabled
    toast.error('Не удалось изменить статус Google Wallet')
  }
}

async function uploadWalletLogo(event) {
  const file = event.target.files?.[0]
  if (!file) return
  walletLogoPreview.value = URL.createObjectURL(file)
  uploadingWalletLogo.value = true
  try {
    const fd = new FormData()
    fd.append('logo', file)
    const res = await api.post(`/core/organizations/${auth.currentOrgId}/upload-wallet-logo/`, fd)
    walletForm.value.logo_url = res.data.logo_url
    walletLogoPreview.value = res.data.logo_url.startsWith('http') ? res.data.logo_url : window.location.origin + res.data.logo_url
    toast.success('Логотип карты загружен')
  } catch {
    toast.error('Ошибка загрузки логотипа')
    walletLogoPreview.value = null
  } finally {
    uploadingWalletLogo.value = false
  }
}

async function uploadBanner(event) {
  const file = event.target.files?.[0]
  if (!file) return
  bannerPreview.value = URL.createObjectURL(file)
  uploadingBanner.value = true
  try {
    const fd = new FormData()
    fd.append('banner', file)
    const res = await api.post(`/core/organizations/${auth.currentOrgId}/upload-banner/`, fd)
    walletForm.value.hero_image_url = res.data.banner_url
    bannerPreview.value = res.data.banner_url.startsWith('http') ? res.data.banner_url : window.location.origin + res.data.banner_url
    toast.success('Баннер карты загружен')
  } catch {
    toast.error('Ошибка загрузки баннера')
    bannerPreview.value = null
  } finally {
    uploadingBanner.value = false
  }
}

async function syncWalletClass() {
  syncingWallet.value = true
  try {
    const logoUrlResolved = walletForm.value.logo_url || (form.value.branding?.logo_url ? (form.value.branding.logo_url.startsWith('http') ? form.value.branding.logo_url : window.location.origin + form.value.branding.logo_url) : '')
    const heroUrlResolved = walletForm.value.hero_image_url ? (walletForm.value.hero_image_url.startsWith('http') ? walletForm.value.hero_image_url : window.location.origin + walletForm.value.hero_image_url) : ''

    const data = {
      issuer_id: walletForm.value.issuer_id,
      class_name: walletForm.value.class_name || form.value.name,
      issuer_name: walletForm.value.issuer_name || form.value.name,
      hex_background_color: walletForm.value.hex_background_color || brandColor.value,
      logo_url: logoUrlResolved,
      hero_image_url: heroUrlResolved,
      locations: walletForm.value.locations || [],
      push_templates: walletForm.value.push_templates || {},
    }
    await api.post(`/core/organizations/${auth.currentOrgId}/google-wallet-class/`, data)
    toast.success('Настройки Google Wallet сохранены и синхронизированы')
  } catch (e) {
    const msg = e.response?.data?.error || 'Ошибка синхронизации'
    toast.error(msg)
  } finally {
    syncingWallet.value = false
  }
}

function openWalletAdvancedModal() {
  if (!walletForm.value.locations) {
    walletForm.value.locations = []
  }
  if (!walletForm.value.push_templates) {
    walletForm.value.push_templates = {
      ru: {
        title: 'Баланс бонусов обновлен',
        body: '{org_name}: начислено +{change} бонусов! Баланс: {balance} б.'
      },
      kz: {
        title: 'Бонус балансы жаңартылды',
        body: '{org_name}: +{change} бонус берілді! Балансыңыз: {balance} балл.'
      }
    }
  }
  showWalletAdvancedModal.value = true
}

function addLocation() {
  const lat = parseFloat(newLocation.value.latitude)
  const lng = parseFloat(newLocation.value.longitude)
  if (isNaN(lat) || lat < -90 || lat > 90) {
    toast.error('Широта (Latitude) должна быть числом от -90 до +90')
    return
  }
  if (isNaN(lng) || lng < -180 || lng > 180) {
    toast.error('Долгота (Longitude) должна быть числом от -180 до +180')
    return
  }
  if ((walletForm.value.locations?.length || 0) >= 10) {
    toast.error('В Google Wallet разрешено максимум 10 гео-точек')
    return
  }
  walletForm.value.locations.push({
    name: newLocation.value.name.trim() || `Филиал #${walletForm.value.locations.length + 1}`,
    latitude: lat,
    longitude: lng
  })
  newLocation.value = { name: '', latitude: '', longitude: '' }
  toast.success('Локация филиала добавлена')
}

function removeLocation(idx) {
  walletForm.value.locations.splice(idx, 1)
}

function insertPushTag(tag) {
  const currentLang = activePushLang.value
  if (!walletForm.value.push_templates) {
    walletForm.value.push_templates = {}
  }
  if (!walletForm.value.push_templates[currentLang]) {
    walletForm.value.push_templates[currentLang] = { title: '', body: '' }
  }
  const currentBody = walletForm.value.push_templates[currentLang].body || ''
  if ((currentBody + ' ' + tag).length <= 200) {
    walletForm.value.push_templates[currentLang].body = currentBody ? `${currentBody} ${tag}` : tag
  } else {
    toast.warning('Превышен лимит длины сообщения (200 символов)')
  }
}

async function saveWalletAdvancedSettings() {
  await syncWalletClass()
  showWalletAdvancedModal.value = false
}

async function toggleAppleWallet() {
  try {
    await api.post(`/core/organizations/${auth.currentOrgId}/apple-wallet-settings/`, {
      is_apple_wallet_enabled: form.value.is_apple_wallet_enabled
    })
    toast.success(form.value.is_apple_wallet_enabled ? 'Apple Wallet включен' : 'Apple Wallet отключен')
  } catch {
    form.value.is_apple_wallet_enabled = !form.value.is_apple_wallet_enabled
    toast.error('Не удалось изменить статус Apple Wallet')
  }
}

async function uploadAppleLogo(event) {
  const file = event.target.files?.[0]
  if (!file) return
  appleLogoPreview.value = URL.createObjectURL(file)
  uploadingAppleLogo.value = true
  try {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('asset_type', 'logo')
    const res = await api.post(`/core/organizations/${auth.currentOrgId}/upload-apple-wallet-asset/`, fd)
    appleWalletForm.value.logo_url = res.data.url
    appleLogoPreview.value = res.data.url.startsWith('http') ? res.data.url : window.location.origin + res.data.url
    toast.success('Логотип Apple Wallet загружен')
  } catch {
    toast.error('Ошибка загрузки логотипа')
    appleLogoPreview.value = null
  } finally {
    uploadingAppleLogo.value = false
  }
}

async function uploadAppleStrip(event) {
  const file = event.target.files?.[0]
  if (!file) return
  appleStripPreview.value = URL.createObjectURL(file)
  uploadingAppleStrip.value = true
  try {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('asset_type', 'strip')
    const res = await api.post(`/core/organizations/${auth.currentOrgId}/upload-apple-wallet-asset/`, fd)
    appleWalletForm.value.strip_url = res.data.url
    appleStripPreview.value = res.data.url.startsWith('http') ? res.data.url : window.location.origin + res.data.url
    toast.success('Баннер Apple Wallet загружен')
  } catch {
    toast.error('Ошибка загрузки баннера')
    appleStripPreview.value = null
  } finally {
    uploadingAppleStrip.value = false
  }
}

function openAppleAdvancedModal() {
  if (!appleWalletForm.value.locations) {
    appleWalletForm.value.locations = []
  }
  if (!appleWalletForm.value.push_templates) {
    appleWalletForm.value.push_templates = {
      ru: {
        change_message: 'Баланс бонусов обновлен: %@ баллов',
        welcome_geo_text: 'Добро пожаловать! Предъявите карту для бонусов.'
      },
      kz: {
        change_message: 'Бонус балансы жаңартылды: %@ балл',
        welcome_geo_text: 'Қош келдіңіз! Бонустарды алу үшін картаңызды көрсетіңіз.'
      }
    }
  }
  showAppleAdvancedModal.value = true
}

function addAppleLocation() {
  const lat = parseFloat(newAppleLocation.value.latitude)
  const lng = parseFloat(newAppleLocation.value.longitude)
  if (isNaN(lat) || lat < -90 || lat > 90) {
    toast.error('Широта (Latitude) должна быть числом от -90 до +90')
    return
  }
  if (isNaN(lng) || lng < -180 || lng > 180) {
    toast.error('Долгота (Longitude) должна быть числом от -180 до +180')
    return
  }
  if ((appleWalletForm.value.locations?.length || 0) >= 10) {
    toast.error('В Apple Wallet разрешено максимум 10 гео-точек')
    return
  }
  appleWalletForm.value.locations.push({
    name: newAppleLocation.value.name.trim() || `Филиал #${appleWalletForm.value.locations.length + 1}`,
    latitude: lat,
    longitude: lng,
    relevant_text: newAppleLocation.value.relevant_text.trim() || 'Предъявите карту для начисления бонусов!'
  })
  newAppleLocation.value = { name: '', latitude: '', longitude: '', relevant_text: '' }
  toast.success('Локация филиала добавлена')
}

function removeAppleLocation(idx) {
  appleWalletForm.value.locations.splice(idx, 1)
}

function insertApplePushTag(tag) {
  const currentLang = activeApplePushLang.value
  if (!appleWalletForm.value.push_templates) {
    appleWalletForm.value.push_templates = {}
  }
  if (!appleWalletForm.value.push_templates[currentLang]) {
    appleWalletForm.value.push_templates[currentLang] = { change_message: '', welcome_geo_text: '' }
  }
  const currentMsg = appleWalletForm.value.push_templates[currentLang].change_message || ''
  appleWalletForm.value.push_templates[currentLang].change_message = currentMsg ? `${currentMsg} ${tag}` : tag
}

async function saveAppleWalletSettings() {
  savingAppleWallet.value = true
  try {
    const data = {
      is_apple_wallet_enabled: form.value.is_apple_wallet_enabled,
      apple_pass_type_id: appleWalletForm.value.pass_type_id,
      apple_team_id: appleWalletForm.value.team_id,
      class_name: appleWalletForm.value.class_name || form.value.name,
      logo_url: appleWalletForm.value.logo_url,
      strip_url: appleWalletForm.value.strip_url,
      barcode_type: appleWalletForm.value.barcode_type || 'barcode',
      background_color: appleWalletForm.value.background_color || '#18181b',
      foreground_color: appleWalletForm.value.foreground_color || '#ffffff',
      label_color: appleWalletForm.value.label_color || '#94a3b8',
      locations: appleWalletForm.value.locations || [],
      push_templates: appleWalletForm.value.push_templates || {}
    }
    const res = await api.post(`/core/organizations/${auth.currentOrgId}/apple-wallet-settings/`, data)
    form.value.is_apple_wallet_enabled = res.data.is_apple_wallet_enabled
    form.value.apple_pass_type_id = res.data.apple_pass_type_id
    form.value.apple_team_id = res.data.apple_team_id
    toast.success('Настройки Apple Wallet успешно сохранены')
  } catch (e) {
    toast.error(e.response?.data?.error || 'Ошибка сохранения Apple Wallet')
  } finally {
    savingAppleWallet.value = false
  }
}

async function saveAppleAdvancedSettings() {
  await saveAppleWalletSettings()
  showAppleAdvancedModal.value = false
}

const programs = ref([])
const programsLoading = ref(false)
const showModal = ref(false)
const modalMode = ref('create')
const modalForm = ref({
  id: null,
  title: '',
  title_kz: '',
  description: '',
  description_kz: ''
})
const submittingProgram = ref(false)
const showDeleteConfirm = ref(false)
const deletingProgram = ref(false)
const programToDelete = ref(null)

async function fetchPrograms() {
  programsLoading.value = true
  try {
    const res = await api.get(`/loyalty/organizations/${auth.currentOrgId}/loyalty-programs/`)
    programs.value = res.data
  } catch {
    toast.error('Не удалось загрузить список программ лояльности')
  } finally {
    programsLoading.value = false
  }
}

function openCreateModal() {
  modalMode.value = 'create'
  modalForm.value = {
    id: null,
    title: '',
    title_kz: '',
    description: '',
    description_kz: ''
  }
  showModal.value = true
}

function openEditModal(prog) {
  modalMode.value = 'edit'
  modalForm.value = {
    id: prog.id,
    title: prog.title,
    title_kz: prog.title_kz || '',
    description: prog.description,
    description_kz: prog.description_kz || ''
  }
  showModal.value = true
}

async function saveProgram() {
  if (!modalForm.value.title.trim()) {
    toast.error('Заголовок обязателен')
    return
  }
  if (!modalForm.value.description.trim()) {
    toast.error('Описание обязательно')
    return
  }

  submittingProgram.value = true
  const data = {
    title: modalForm.value.title,
    title_kz: modalForm.value.title_kz || null,
    description: modalForm.value.description,
    description_kz: modalForm.value.description_kz || null
  }

  try {
    if (modalMode.value === 'create') {
      await api.post(`/loyalty/organizations/${auth.currentOrgId}/loyalty-programs/`, data)
      toast.success('Программа лояльности создана')
    } else {
      await api.put(`/loyalty/organizations/${auth.currentOrgId}/loyalty-programs/${modalForm.value.id}/`, data)
      toast.success('Программа лояльности обновлена')
    }
    showModal.value = false
    await fetchPrograms()
  } catch {
    toast.error('Ошибка сохранения программы лояльности')
  } finally {
    submittingProgram.value = false
  }
}

function confirmDelete(prog) {
  programToDelete.value = prog
  showDeleteConfirm.value = true
}

async function deleteProgram() {
  if (!programToDelete.value) return
  deletingProgram.value = true
  try {
    await api.delete(`/loyalty/organizations/${auth.currentOrgId}/loyalty-programs/${programToDelete.value.id}/`)
    toast.success('Программа лояльности удалена')
    showDeleteConfirm.value = false
    await fetchPrograms()
  } catch {
    toast.error('Не удалось удалить программу лояльности')
  } finally {
    deletingProgram.value = false
  }
}

// --- WhatsApp WABA Integration Logic ---
const showWabaToken = ref(false)
const loadingWabaTemplates = ref(false)
const wabaTemplates = ref([])
const templateSearchQuery = ref('')
const loadingWabaNumbers = ref(false)
const wabaPhoneNumbers = ref([])

const wabaRules = ref([])
const loadingWabaRules = ref(false)
const wabaLogs = ref([])
const loadingWabaLogs = ref(false)
const showWabaLogsModal = ref(false)
const exportingWabaLogs = ref(false)
const wabaLogsTotalCount = ref(0)
const wabaLogFilters = ref({
  startDate: '',
  endDate: '',
  status: '',
  search: ''
})

const showRuleModal = ref(false)
const ruleModalMode = ref('create')
const savingRule = ref(false)
const ruleForm = ref({
  id: null,
  name: '',
  event_type: 'auth_code',
  is_enabled: true,
  template_name: '',
  template_language: 'ru',
  parameter_mappings: {
    header: [],
    body: [],
    buttons: []
  }
})

const showWabaTestModal = ref(false)
const wabaTestPhone = ref('')
const wabaTestTemplate = ref('')
const sendingWabaTest = ref(false)

const webhookSourceOptions = [
  { value: 'auth_code', label: '🔑 Код авторизации (только цифры из текста)' },
  { value: 'sum', label: '💰 Сумма операции (body.sum)' },
  { value: 'sum_abs', label: '💰 Сумма операции без знака (-) (Math.abs)' },
  { value: 'balance', label: '💳 Текущий баланс (body.balance)' },
  { value: 'balance_text_smart', label: '✨ Умный текст баланса (Пополнен/Списан на X тенге)' },
  { value: 'phone', label: '📱 Номер телефона (body.phone)' },
  { value: 'restaurant_name', label: '🏢 Название ресторана (organization.name)' },
  { value: 'text', label: '📄 Полный текст сообщения (body.text)' },
  { value: 'text_line_1', label: '1️⃣ Первая строка текста' },
  { value: 'text_line_2', label: '2️⃣ Вторая строка текста' },
  { value: 'static', label: '✏️ Свой постоянный текст...' },
]

const authCodeRule = computed(() => wabaRules.value.find(r => r.event_type === 'auth_code'))
const balanceRule = computed(() => wabaRules.value.find(r => r.event_type === 'balance'))
const pushRule = computed(() => wabaRules.value.find(r => r.event_type === 'push'))

const approvedTemplates = computed(() => {
  return wabaTemplates.value.filter(t => t.status === 'APPROVED' || !t.status)
})

const filteredTemplates = computed(() => {
  if (!templateSearchQuery.value.trim()) return wabaTemplates.value
  const q = templateSearchQuery.value.toLowerCase()
  return wabaTemplates.value.filter(t => 
    (t.name && t.name.toLowerCase().includes(q)) ||
    (t.category && t.category.toLowerCase().includes(q))
  )
})

const selectedTemplateObj = computed(() => {
  if (!ruleForm.value.template_name) return null
  return wabaTemplates.value.find(t => t.name === ruleForm.value.template_name) || null
})

function getTemplateBodyText(template) {
  if (!template || !template.components) return ''
  const bodyComp = template.components.find(c => c.type === 'BODY')
  return bodyComp?.text || ''
}

function getTemplateHeaderText(template) {
  if (!template || !template.components) return ''
  const headerComp = template.components.find(c => c.type === 'HEADER')
  return headerComp?.text || ''
}

function getTemplateButtons(template) {
  if (!template || !template.components) return []
  const btnComp = template.components.find(c => c.type === 'BUTTONS')
  if (!btnComp || !btnComp.buttons) return []
  return btnComp.buttons.map((b, idx) => ({
    index: idx,
    type: b.type,
    text: b.text,
    url: b.url,
    hasVariable: b.url && b.url.includes('{{1}}')
  }))
}

function getTemplateBodyVars(template) {
  if (!template || !template.components) return []
  const bodyComp = template.components.find(c => c.type === 'BODY')
  if (!bodyComp || !bodyComp.text) return []
  const matches = bodyComp.text.match(/\{\{(\d+)\}\}/g) || []
  const uniqueIndexes = [...new Set(matches.map(m => m.replace(/[{}]/g, '')))]
  return uniqueIndexes.sort((a, b) => Number(a) - Number(b))
}

function getTemplateHeaderVars(template) {
  if (!template || !template.components) return []
  const headerComp = template.components.find(c => c.type === 'HEADER')
  if (!headerComp || headerComp.format !== 'TEXT' || !headerComp.text) return []
  const matches = headerComp.text.match(/\{\{(\d+)\}\}/g) || []
  return matches.map(m => m.replace(/[{}]/g, ''))
}

function onTemplateSelected() {
  const t = selectedTemplateObj.value
  if (!t) return
  ruleForm.value.template_language = t.language || 'ru'
  
  const headerVars = getTemplateHeaderVars(t)
  const bodyVars = getTemplateBodyVars(t)
  const buttons = getTemplateButtons(t).filter(b => b.hasVariable)
  
  const currentMappings = ruleForm.value.parameter_mappings || {}
  
  const header = headerVars.map(v => {
    const existing = (currentMappings.header || []).find(h => h.param === v)
    return existing || { param: v, source: 'restaurant_name', static_value: '' }
  })
  
  const body = bodyVars.map(v => {
    const existing = (currentMappings.body || []).find(b => b.param === v)
    let defaultSource = 'text'
    if (ruleForm.value.event_type === 'auth_code' && v === '1') defaultSource = 'auth_code'
    else if (ruleForm.value.event_type === 'balance' && v === '1') defaultSource = 'balance_text_smart'
    else if (ruleForm.value.event_type === 'balance' && v === '2') defaultSource = 'balance'
    return existing || { param: v, source: defaultSource, static_value: '' }
  })
  
  const btnMappings = buttons.map(b => {
    const existing = (currentMappings.buttons || []).find(btn => btn.index === b.index)
    let defaultSource = ruleForm.value.event_type === 'auth_code' ? 'auth_code' : 'static'
    return existing || { index: b.index, sub_type: 'url', source: defaultSource, static_value: '' }
  })
  
  ruleForm.value.parameter_mappings = { header, body, buttons: btnMappings }
}

async function fetchWabaTemplates() {
  if (!form.value.waba_access_token || !form.value.waba_business_account_id) {
    toast.error('Сначала укажите и сохраните Access Token и Business Account ID')
    return
  }
  loadingWabaTemplates.value = true
  try {
    const res = await api.get(`/core/organizations/${auth.currentOrgId}/waba/templates/`)
    wabaTemplates.value = res.data.templates || []
    toast.success(`Успешно загружено ${wabaTemplates.value.length} шаблонов из Meta`)
  } catch (e) {
    toast.error(e.response?.data?.error || 'Не удалось загрузить шаблоны из Meta')
  } finally {
    loadingWabaTemplates.value = false
  }
}

async function fetchWabaPhoneNumbers() {
  if (!form.value.waba_access_token || !form.value.waba_business_account_id) {
    toast.error('Сначала укажите и сохраните Access Token и Business Account ID')
    return
  }
  loadingWabaNumbers.value = true
  try {
    const res = await api.get(`/core/organizations/${auth.currentOrgId}/waba/phone-numbers/`)
    wabaPhoneNumbers.value = res.data.phone_numbers || []
    if (wabaPhoneNumbers.value.length > 0 && !form.value.waba_phone_number_id) {
      form.value.waba_phone_number_id = wabaPhoneNumbers.value[0].id
    }
    toast.success(`Найдено ${wabaPhoneNumbers.value.length} телефонных номеров`)
  } catch (e) {
    toast.error(e.response?.data?.error || 'Не удалось загрузить телефонные номера из Meta')
  } finally {
    loadingWabaNumbers.value = false
  }
}

async function loadWabaRules() {
  loadingWabaRules.value = true
  try {
    const res = await api.get(`/core/organizations/${auth.currentOrgId}/waba/rules/`)
    wabaRules.value = res.data || []
  } catch {
    console.error('Failed to load WABA rules')
  } finally {
    loadingWabaRules.value = false
  }
}

async function loadWabaLogs() {
  loadingWabaLogs.value = true
  try {
    const res = await api.get(`/core/organizations/${auth.currentOrgId}/waba/logs/`, {
      params: { limit: 100 }
    })
    wabaLogs.value = res.data.logs || []
    wabaLogsTotalCount.value = res.data.total_count || wabaLogs.value.length
  } catch {
    console.error('Failed to load WABA logs')
  } finally {
    loadingWabaLogs.value = false
  }
}

function openWabaLogsModal() {
  showWabaLogsModal.value = true
  loadWabaLogsFiltered()
}

function resetWabaLogFilters() {
  wabaLogFilters.value = {
    startDate: '',
    endDate: '',
    status: '',
    search: ''
  }
  loadWabaLogsFiltered()
}

async function loadWabaLogsFiltered() {
  loadingWabaLogs.value = true
  try {
    const params = {
      limit: 100,
      start_date: wabaLogFilters.value.startDate || undefined,
      end_date: wabaLogFilters.value.endDate || undefined,
      status: wabaLogFilters.value.status || undefined,
      search: wabaLogFilters.value.search?.trim() || undefined
    }
    const res = await api.get(`/core/organizations/${auth.currentOrgId}/waba/logs/`, { params })
    wabaLogs.value = res.data.logs || []
    wabaLogsTotalCount.value = res.data.total_count || wabaLogs.value.length
  } catch (e) {
    console.error('Failed to load WABA logs:', e)
    toast.error('Не удалось загрузить журнал сообщений')
  } finally {
    loadingWabaLogs.value = false
  }
}

async function exportWabaLogsExcel() {
  exportingWabaLogs.value = true
  try {
    const params = {
      export: 'excel',
      start_date: wabaLogFilters.value.startDate || undefined,
      end_date: wabaLogFilters.value.endDate || undefined,
      status: wabaLogFilters.value.status || undefined,
      search: wabaLogFilters.value.search?.trim() || undefined
    }
    const res = await api.get(`/core/organizations/${auth.currentOrgId}/waba/logs/`, {
      params,
      responseType: 'blob'
    })
    const blob = new Blob([res.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const startStr = wabaLogFilters.value.startDate || 'all'
    const endStr = wabaLogFilters.value.endDate || new Date().toISOString().slice(0, 10)
    a.download = `waba_logs_${auth.currentOrgId}_${startStr}_to_${endStr}.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    toast.success('Отчёт Excel успешно выгружен')
  } catch (e) {
    console.error('Failed to export WABA logs:', e)
    toast.error('Не удалось выгрузить журнал в Excel')
  } finally {
    exportingWabaLogs.value = false
  }
}

function formatEventType(type) {
  const map = {
    auth_code: 'Код авторизации',
    balance: 'Баланс кошелька',
    push: 'Пуш-уведомление',
    custom: 'Пользовательский'
  }
  return map[type] || type || 'Событие'
}

async function loadWabaData() {
  await Promise.all([loadWabaRules(), loadWabaLogs()])
}

function openCreateRuleModal(presetType = null) {
  ruleModalMode.value = 'create'
  let ruleName = 'Новое правило WABA'
  let eventType = 'custom'
  if (presetType === 'auth_code') {
    ruleName = 'Отправка кода авторизации'
    eventType = 'auth_code'
  } else if (presetType === 'balance') {
    ruleName = 'Уведомление об изменении баланса'
    eventType = 'balance'
  } else if (presetType === 'push') {
    ruleName = 'Информационный пуш'
    eventType = 'push'
  }

  let firstTmpl = approvedTemplates.value[0]?.name || ''
  let firstLang = approvedTemplates.value[0]?.language || 'ru'

  ruleForm.value = {
    id: null,
    name: ruleName,
    event_type: eventType,
    is_enabled: true,
    template_name: firstTmpl,
    template_language: firstLang,
    parameter_mappings: { header: [], body: [], buttons: [] }
  }

  if (firstTmpl) {
    onTemplateSelected()
  }

  showRuleModal.value = true
}

function openCreateRuleModalWithTemplate(template) {
  ruleModalMode.value = 'create'
  ruleForm.value = {
    id: null,
    name: `Сценарий: ${template.name}`,
    event_type: 'custom',
    is_enabled: true,
    template_name: template.name,
    template_language: template.language || 'ru',
    parameter_mappings: { header: [], body: [], buttons: [] }
  }
  onTemplateSelected()
  showRuleModal.value = true
}

function openEditRuleModal(rule) {
  ruleModalMode.value = 'edit'
  ruleForm.value = {
    id: rule.id,
    name: rule.name,
    event_type: rule.event_type,
    is_enabled: rule.is_enabled,
    template_name: rule.template_name,
    template_language: rule.template_language || 'ru',
    parameter_mappings: JSON.parse(JSON.stringify(rule.parameter_mappings || { header: [], body: [], buttons: [] }))
  }
  showRuleModal.value = true
}

async function saveRule() {
  if (!ruleForm.value.template_name) {
    toast.error('Выберите шаблон Meta')
    return
  }
  savingRule.value = true
  try {
    const payload = {
      name: ruleForm.value.name,
      event_type: ruleForm.value.event_type,
      is_enabled: ruleForm.value.is_enabled,
      template_name: ruleForm.value.template_name,
      template_language: ruleForm.value.template_language,
      parameter_mappings: ruleForm.value.parameter_mappings
    }

    if (ruleModalMode.value === 'create') {
      await api.post(`/core/organizations/${auth.currentOrgId}/waba/rules/`, payload)
      toast.success('Правило отправки успешно создано')
    } else {
      await api.patch(`/core/organizations/${auth.currentOrgId}/waba/rules/${ruleForm.value.id}/`, payload)
      toast.success('Правило отправки успешно обновлено')
    }
    showRuleModal.value = false
    await loadWabaRules()
  } catch (e) {
    toast.error(e.response?.data?.error || 'Не удалось сохранить правило')
  } finally {
    savingRule.value = false
  }
}

async function toggleRule(rule) {
  try {
    await api.patch(`/core/organizations/${auth.currentOrgId}/waba/rules/${rule.id}/`, {
      is_enabled: !rule.is_enabled
    })
    rule.is_enabled = !rule.is_enabled
    toast.success(`Правило "${rule.name}" ${rule.is_enabled ? 'включено' : 'отключено'}`)
  } catch {
    toast.error('Ошибка изменения статуса правила')
  }
}

async function deleteRule(rule) {
  if (!confirm(`Удалить правило "${rule.name}"?`)) return
  try {
    await api.delete(`/core/organizations/${auth.currentOrgId}/waba/rules/${rule.id}/`)
    toast.success('Правило удалено')
    await loadWabaRules()
  } catch {
    toast.error('Не удалось удалить правило')
  }
}

function openWabaTestModal() {
  wabaTestPhone.value = ''
  wabaTestTemplate.value = approvedTemplates.value[0]?.name || ''
  showWabaTestModal.value = true
}

async function sendWabaTest() {
  if (!wabaTestPhone.value.trim()) {
    toast.error('Укажите номер телефона')
    return
  }
  if (!wabaTestTemplate.value) {
    toast.error('Выберите шаблон')
    return
  }
  if (form.value.waba_phone_number_id && form.value.waba_business_account_id && form.value.waba_phone_number_id === form.value.waba_business_account_id) {
    toast.error('В настройках Phone Number ID совпадает с Business Account ID! Нажмите «⚡ Загрузить из Meta» рядом с полем Phone Number ID.')
    return
  }
  if (form.value.waba_phone_number_id && (form.value.waba_phone_number_id.startsWith('+') || form.value.waba_phone_number_id.length <= 12)) {
    toast.error('В настройках в поле Phone Number ID указан телефонный номер, а требуется числовой Phone Number ID из Meta. Нажмите «⚡ Загрузить из Meta».')
    return
  }
  sendingWabaTest.value = true
  try {
    const res = await api.post(`/core/organizations/${auth.currentOrgId}/waba/send-test/`, {
      phone: wabaTestPhone.value.trim(),
      template_name: wabaTestTemplate.value
    })
    toast.success(res.data.message || 'Тестовое сообщение отправлено!')
    showWabaTestModal.value = false
    await loadWabaLogs()
  } catch (e) {
    toast.error(e.response?.data?.error || 'Ошибка отправки тестового сообщения')
  } finally {
    sendingWabaTest.value = false
  }
}

function formatLogDate(dateStr) {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return d.toLocaleString('ru-RU', { hour12: false })
  } catch {
    return dateStr
  }
}

// Watch activeTab to load list lazily
watch(activeTab, (newTab) => {
  if (newTab === 'loyalty_programs') {
    fetchPrograms()
  } else if (newTab === 'waba') {
    loadWabaData()
  } else if (newTab === 'card_tiers') {
    fetchIikoWallets()
  }
})

onMounted(load)
</script>

<style scoped>
.form-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  color: #94a3b8;
  margin-bottom: 0.375rem;
}
.form-input {
  width: 100%;
  background-color: #1e293b;
  border: 1px solid #334155;
  color: white;
  border-radius: 0.75rem;
  padding: 0.75rem 1rem;
  font-size: 0.875rem;
  transition: all 0.15s;
  outline: none;
}
.form-input:focus {
  box-shadow: 0 0 0 2px rgba(99,102,241,0.5);
  border-color: transparent;
}
.form-input::placeholder {
  color: #64748b;
}

/* 3D Loyalty Card Flip Animation */
.card-perspective {
  perspective: 1200px;
  -webkit-perspective: 1200px;
}

.card-flipper {
  position: relative;
  width: 100%;
  transform-style: preserve-3d;
  -webkit-transform-style: preserve-3d;
  transition: transform 0.65s cubic-bezier(0.4, 0.2, 0.2, 1);
  cursor: pointer;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

.card-flipper.is-flipped {
  transform: rotateY(180deg);
  -webkit-transform: rotateY(180deg);
}

.card-face {
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  width: 100%;
}

.card-front {
  position: relative;
  z-index: 2;
  transform: rotateY(0deg);
  -webkit-transform: rotateY(0deg);
}

.card-back {
  position: absolute;
  inset: 0;
  transform: rotateY(180deg);
  -webkit-transform: rotateY(180deg);
}
</style>

