<template>
  <div class="p-8 max-w-4xl">
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-white">Настройки организации</h1>
      <p class="text-slate-400 text-sm mt-1">Управление конфигурацией ресторана</p>
    </div>

    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-8 h-8 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
    </div>

    <div v-else>
      <!-- Tabs -->
      <div class="flex bg-slate-800 rounded-xl p-1 mb-6 gap-1 w-fit">
        <button v-for="tab in tabs" :key="tab.id"
          :id="`tab-settings-${tab.id}`"
          @click="activeTab = tab.id"
          class="px-5 py-2 text-sm font-medium rounded-lg transition-all duration-200"
          :class="activeTab === tab.id ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white'"
        >{{ tab.label }}</button>
      </div>

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
        <div>
          <label class="form-label">Ссылка на логотип (Logo URL)</label>
          <input v-model="walletForm.logo_url" type="url" class="form-input" placeholder="https://..." />
          <p class="text-xs text-slate-500 mt-1">Квадратное фото (PNG), мин. 660×660 px. Отображается в круглом бейдже вверху карты. Если пусто, используется логотип из вкладки Брендинг.</p>
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
        <div class="flex justify-end pt-2">
          <SaveButton :saving="syncingWallet" @save="syncWalletClass" />
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import SaveButton from '@/components/SaveButton.vue'

const auth = useAuthStore()
const toast = useToastStore()

const tabs = computed(() => {
  const list = [
    { id: 'general', label: 'Основные / Telegram' },
    { id: 'waba', label: 'Настройка WABA' },
    { id: 'iiko', label: 'Интеграция iiko Cloud API' },
    { id: 'iiko_server', label: 'Интеграция iiko Server API' },
  ]
  if (form.value.is_loyalty_enabled) {
    list.push(
      { id: 'branding', label: 'Брендинг TMA' },
      { id: 'wallet', label: 'Google Wallet' },
      { id: 'loyalty_programs', label: 'Программа лояльности' }
    )
  }
  if (form.value.is_ai_agent_enabled) {
    list.push({ id: 'llm', label: 'Настройки LLM' })
  }
  return list
})
const activeTab = ref('general')
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
const uploadingBanner = ref(false)
const bannerPreview = ref(null)
const walletForm = ref({
  issuer_id: '',
  class_name: '',
  issuer_name: '',
  logo_url: '',
  hero_image_url: '',
  hex_background_color: '#000000'
})

const form = ref({
  name: '', slug: '', address: '',
  tg_bot_token: '', tg_bot_username: '', tma_name: '', tma_direct_link: '',
  is_google_wallet_enabled: false,
  is_waba_enabled: false,
  waba_access_token: '',
  waba_business_account_id: '',
  waba_phone_number_id: '',
  iiko_integration_type: 'iiko_transport',
  iiko_api_base_url: 'https://api-ru.iiko.services/api/1',
  iiko_api_login: '', iiko_app_id: '', iiko_client_secret: '', iiko_organization_id: '', iiko_loyalty_program_id: '',
  is_iiko_webhook_password_enabled: false, iiko_webhook_password: '',
  iiko_server_url: '', iiko_server_login: '', iiko_server_password: '',
  branding: {},
  instagram_link: '', whatsapp_link: '',
  is_loyalty_enabled: true, is_analytics_enabled: false, is_ai_agent_enabled: false,
  llm_provider: 'openai', llm_model_name: 'gpt-4o-mini', llm_api_key: '', llm_system_prompt: '',
})

const brandColor = computed({
  get: () => form.value.branding?.design_color || '#6366f1',
  set: (v) => { form.value.branding = { ...form.value.branding, design_color: v } },
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
    }
    if (walletForm.value.hero_image_url) {
      bannerPreview.value = walletForm.value.hero_image_url.startsWith('http') 
        ? walletForm.value.hero_image_url 
        : window.location.origin + walletForm.value.hero_image_url
    }
    
    initLlmModelFields()
    
    if (form.value.is_analytics_enabled) {
      await loadPresets()
    }
    if (activeTab.value === 'waba') {
      await loadWabaData()
    }
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
</style>

