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

      <!-- TAB: iiko Integration -->
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
          <label class="form-label">iiko API Login (токен)</label>
          <input id="input-iiko-login" v-model="form.iiko_api_login" type="password" class="form-input" placeholder="••••••••••" />
        </div>
        <div>
          <label class="form-label">iiko Organization ID</label>
          <input id="input-iiko-org-id" v-model="form.iiko_organization_id" type="text" class="form-input font-mono text-sm"
            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            pattern="[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
            title="UUID формат" />
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
        <div class="flex justify-end pt-2">
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
        <div>
          <label class="form-label">Google Issuer ID</label>
          <input v-model="walletForm.issuer_id" type="text" class="form-input" placeholder="Например: 3388000000000000000" />
          <p class="text-xs text-slate-500 mt-1">Необходим для генерации карт лояльности</p>
        </div>
        <div>
          <label class="form-label">Название программы (Loyalty Class)</label>
          <input v-model="walletForm.class_name" type="text" class="form-input" placeholder="Например: Ресторан Ромашка" />
        </div>
        <div>
          <label class="form-label">Имя издателя (Issuer Name)</label>
          <input v-model="walletForm.issuer_name" type="text" class="form-input" placeholder="Например: ООО Ромашка" />
        </div>
        <div>
          <label class="form-label">Ссылка на логотип (Logo URL)</label>
          <input v-model="walletForm.logo_url" type="url" class="form-input" placeholder="https://..." />
          <p class="text-xs text-slate-500 mt-1">Если пусто, используется логотип из вкладки Брендинг. Загрузите логотип в интернет, Google не принимает localhost.</p>
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

const tabs = [
  { id: 'general', label: 'Основные / Telegram' },
  { id: 'iiko', label: 'Интеграция iiko' },
  { id: 'branding', label: 'Брендинг TMA' },
  { id: 'wallet', label: 'Google Wallet' },
  { id: 'loyalty_programs', label: 'Программа лояльности' },
]
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
const walletForm = ref({
  issuer_id: '',
  class_name: '',
  issuer_name: '',
  logo_url: '',
  hex_background_color: '#000000'
})

const form = ref({
  name: '', slug: '', address: '',
  tg_bot_token: '', tg_bot_username: '', tma_name: '', tma_direct_link: '',
  iiko_integration_type: 'iiko_transport',
  iiko_api_base_url: 'https://api-ru.iiko.services/api/1',
  iiko_api_login: '', iiko_organization_id: '', iiko_loyalty_program_id: '',
  is_iiko_webhook_password_enabled: false, iiko_webhook_password: '',
  branding: {},
  instagram_link: '', whatsapp_link: '',
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

async function load() {
  try {
    const res = await api.get(`/core/organizations/${auth.currentOrgId}/settings/`)
    form.value = { ...form.value, ...res.data }
    walletForm.value.issuer_id = res.data.google_issuer_id || ''
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
      iiko_integration_type: form.value.iiko_integration_type,
      iiko_api_base_url: form.value.iiko_api_base_url,
      iiko_api_login: form.value.iiko_api_login || undefined,
      iiko_organization_id: form.value.iiko_organization_id || null,
      iiko_loyalty_program_id: form.value.iiko_loyalty_program_id || null,
      is_iiko_webhook_password_enabled: form.value.is_iiko_webhook_password_enabled,
      iiko_webhook_password: form.value.iiko_webhook_password || null,
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

async function syncWalletClass() {
  syncingWallet.value = true
  try {
    const data = {
      issuer_id: walletForm.value.issuer_id,
      class_name: walletForm.value.class_name || form.value.name,
      issuer_name: walletForm.value.issuer_name || form.value.name,
      hex_background_color: walletForm.value.hex_background_color || brandColor.value,
      logo_url: walletForm.value.logo_url || (form.value.branding?.logo_url ? window.location.origin + form.value.branding.logo_url : '')
    }
    await api.post(`/core/organizations/${auth.currentOrgId}/google-wallet-class/`, data)
    toast.success('Настройки Google Wallet синхронизированы')
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

// Watch activeTab to load list lazily
watch(activeTab, (newTab) => {
  if (newTab === 'loyalty_programs') {
    fetchPrograms()
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

