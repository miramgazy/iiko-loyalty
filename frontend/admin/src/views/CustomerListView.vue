<template>
  <div class="p-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-white">База клиентов</h1>
        <p class="text-slate-400 text-sm mt-1">Участники программы лояльности</p>
      </div>
      <div class="flex flex-wrap items-center gap-3">
        <button id="btn-sync-all" @click="syncAllCustomers" :disabled="syncingAll || pushingAll"
          title="Запросить данные из iiko для клиентов без имени"
          class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
          <svg class="w-4 h-4" :class="{ 'animate-spin': syncingAll }" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {{ syncingAll ? 'Синхронизация...' : '🔄 Обновить из iiko (без имени)' }}
        </button>
        <button id="btn-push-all" @click="pushAllCustomers" :disabled="syncingAll || pushingAll"
          class="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
          <svg v-if="pushingAll" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
          </svg>
          {{ pushingAll ? 'Выгрузка...' : '📤 Выгрузить всех в iiko' }}
        </button>
        <button id="btn-export-csv" @click="exportCSV"
          class="border border-slate-700 text-slate-300 hover:text-white hover:bg-slate-800 px-4 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center gap-2">
          📥 Экспорт CSV
        </button>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
      <div v-for="stat in stats" :key="stat.label" class="bg-slate-900 rounded-xl border border-slate-800 px-5 py-4">
        <p class="text-xs text-slate-500 mb-1">{{ stat.label }}</p>
        <p class="text-2xl font-bold text-white">{{ stat.value }}</p>
      </div>
    </div>

    <!-- Wallet Cards Overview Tile -->
    <div class="bg-slate-900 rounded-2xl border border-slate-800 p-5 mb-6">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
            </svg>
          </div>
          <div>
            <h2 class="text-base font-semibold text-white">Карты кошелька (Wallet)</h2>
            <p class="text-xs text-slate-400">Суммарная статистика добавления карт лояльности в кошельки клиентов</p>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <div class="flex items-center gap-2">
            <span class="text-xs text-slate-400">Установили карту:</span>
            <span class="text-xs font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-2.5 py-1 rounded-lg">
              {{ totalWithWallet }} ({{ totalWithWalletPercent }}%)
            </span>
          </div>
          <button v-if="selectedWalletFilter" @click="setWalletFilter('')" class="text-xs text-indigo-400 hover:text-indigo-300 underline">
            Сбросить фильтр
          </button>
        </div>
      </div>

      <!-- 3 summary cards inside the tile -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <!-- Google Wallet -->
        <div 
          @click="setWalletFilter(selectedWalletFilter === 'google' ? '' : 'google')"
          class="cursor-pointer relative overflow-hidden rounded-xl border p-4 transition-all duration-200"
          :class="selectedWalletFilter === 'google' 
            ? 'bg-sky-950/40 border-sky-500 ring-1 ring-sky-500' 
            : 'bg-slate-800/60 border-slate-700/60 hover:bg-slate-800 hover:border-slate-600'"
        >
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2.5">
              <span class="w-8 h-8 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 text-sm font-bold">
                G
              </span>
              <span class="text-sm font-semibold text-white">Google Wallet</span>
            </div>
            <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-sky-950 text-sky-400 border border-sky-800">
              {{ walletPercent(statsData.google_wallet) }}%
            </span>
          </div>
          <div class="flex items-baseline justify-between mt-3">
            <span class="text-2xl font-bold text-white">{{ statsData.google_wallet || 0 }}</span>
            <span class="text-xs text-slate-400">клиентов</span>
          </div>
          <div class="w-full bg-slate-700/50 rounded-full h-1.5 mt-2 overflow-hidden">
            <div class="bg-sky-400 h-1.5 rounded-full transition-all duration-500" :style="{ width: walletPercent(statsData.google_wallet) + '%' }"></div>
          </div>
        </div>

        <!-- Apple Wallet -->
        <div 
          @click="setWalletFilter(selectedWalletFilter === 'apple' ? '' : 'apple')"
          class="cursor-pointer relative overflow-hidden rounded-xl border p-4 transition-all duration-200"
          :class="selectedWalletFilter === 'apple' 
            ? 'bg-zinc-800/80 border-zinc-400 ring-1 ring-zinc-400' 
            : 'bg-slate-800/60 border-slate-700/60 hover:bg-slate-800 hover:border-slate-600'"
        >
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2.5">
              <span class="w-8 h-8 rounded-lg bg-zinc-700/50 border border-zinc-600/50 flex items-center justify-center text-zinc-200 text-base">
                
              </span>
              <span class="text-sm font-semibold text-white">Apple Wallet</span>
            </div>
            <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300 border border-zinc-700">
              {{ walletPercent(statsData.apple_wallet) }}%
            </span>
          </div>
          <div class="flex items-baseline justify-between mt-3">
            <span class="text-2xl font-bold text-white">{{ statsData.apple_wallet || 0 }}</span>
            <span class="text-xs text-slate-400">клиентов</span>
          </div>
          <div class="w-full bg-slate-700/50 rounded-full h-1.5 mt-2 overflow-hidden">
            <div class="bg-zinc-300 h-1.5 rounded-full transition-all duration-500" :style="{ width: walletPercent(statsData.apple_wallet) + '%' }"></div>
          </div>
        </div>

        <!-- Without Wallet -->
        <div 
          @click="setWalletFilter(selectedWalletFilter === 'none' ? '' : 'none')"
          class="cursor-pointer relative overflow-hidden rounded-xl border p-4 transition-all duration-200"
          :class="selectedWalletFilter === 'none' 
            ? 'bg-amber-950/30 border-amber-600 ring-1 ring-amber-600' 
            : 'bg-slate-800/60 border-slate-700/60 hover:bg-slate-800 hover:border-slate-600'"
        >
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2.5">
              <span class="w-8 h-8 rounded-lg bg-slate-700/40 border border-slate-600/40 flex items-center justify-center text-slate-400 text-sm">
                ✕
              </span>
              <span class="text-sm font-semibold text-slate-300">Не установлена</span>
            </div>
            <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
              {{ walletPercent(statsData.no_wallet) }}%
            </span>
          </div>
          <div class="flex items-baseline justify-between mt-3">
            <span class="text-2xl font-bold text-slate-300">{{ statsData.no_wallet || 0 }}</span>
            <span class="text-xs text-slate-400">клиентов</span>
          </div>
          <div class="w-full bg-slate-700/50 rounded-full h-1.5 mt-2 overflow-hidden">
            <div class="bg-slate-500 h-1.5 rounded-full transition-all duration-500" :style="{ width: walletPercent(statsData.no_wallet) + '%' }"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Search & Filters -->
    <div class="flex flex-wrap items-center justify-between gap-4 mb-5">
      <div class="relative max-w-sm flex-1 min-w-[260px]">
        <span class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">🔍</span>
        <input
          id="input-customer-search"
          v-model="search"
          type="text"
          placeholder="Поиск по имени или телефону..."
          class="w-full bg-slate-900 border border-slate-800 text-white rounded-xl pl-10 pr-4 py-3 text-sm
                 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent
                 placeholder:text-slate-500 transition-all"
          @input="debouncedSearch"
        />
      </div>

      <div v-if="selectedWalletFilter" class="flex items-center gap-2 bg-slate-900 border border-slate-800 px-3 py-2 rounded-xl">
        <span class="text-xs text-slate-400">Фильтр по карте:</span>
        <span class="text-xs font-semibold px-2.5 py-1 rounded-lg"
          :class="selectedWalletFilter === 'google'
            ? 'bg-sky-950 text-sky-400 border border-sky-800'
            : selectedWalletFilter === 'apple'
              ? 'bg-zinc-800 text-zinc-300 border border-zinc-700'
              : 'bg-slate-800 text-slate-400 border border-slate-700'">
          {{ selectedWalletFilter === 'google' ? 'Google Wallet' : selectedWalletFilter === 'apple' ? 'Apple Wallet' : 'Без карты' }}
        </span>
        <button @click="setWalletFilter('')" class="text-xs text-slate-500 hover:text-white ml-1">✕</button>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden">
      <div v-if="loading" class="flex items-center justify-center py-20">
        <div class="w-8 h-8 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
      </div>
      <div v-else>
        <div class="overflow-x-auto">
          <table class="w-full min-w-[1240px] divide-y divide-slate-800 text-left border-collapse">
          <thead>
            <tr class="border-b border-slate-800 bg-slate-900/60">
              <th class="text-left px-5 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider w-[240px] min-w-[220px]">Клиент</th>
              <th class="text-left px-4 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider w-[160px] min-w-[150px] whitespace-nowrap">Телефон</th>
              <th class="text-left px-4 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider w-[160px] min-w-[150px] whitespace-nowrap">Баллы / Кошельки</th>
              <th class="text-left px-4 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider w-[150px] min-w-[140px] whitespace-nowrap">Тип карты</th>
              <th class="text-left px-4 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider w-[140px] min-w-[130px] whitespace-nowrap">Онбординг</th>
              <th class="text-left px-4 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider w-[170px] min-w-[160px]">iiko</th>
              <th class="text-left px-4 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider w-[130px] min-w-[120px] whitespace-nowrap">Рассылка</th>
              <th class="text-left px-4 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider w-[120px] min-w-[110px] whitespace-nowrap">Дата</th>
              <th class="text-center px-4 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider w-[110px] min-w-[100px] whitespace-nowrap">Действие</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800">
            <tr v-for="c in customers" :key="c.id" class="hover:bg-slate-800/50 transition-colors">
              <td class="px-5 py-4 w-[240px] min-w-[220px]">
                <div class="flex items-center gap-3">
                  <div class="w-9 h-9 rounded-full bg-slate-700 flex items-center justify-center flex-shrink-0">
                    <span class="text-slate-300 text-xs font-bold">{{ initials(c) }}</span>
                  </div>
                  <div class="min-w-0">
                    <p class="font-medium text-white text-sm truncate" :title="`${c.first_name || ''} ${c.last_name || ''}`">
                      {{ c.first_name || 'Без имени' }} {{ c.last_name || '' }}
                    </p>
                    <p class="text-slate-500 text-xs truncate">TG: {{ c.telegram_id || '—' }}</p>
                  </div>
                </div>
              </td>
              <td class="px-4 py-4 w-[160px] min-w-[150px] whitespace-nowrap">
                <span v-if="c.phone" class="text-sm text-slate-300 font-mono">{{ c.phone }}</span>
                <span v-else class="text-xs text-amber-500 bg-amber-950/40 border border-amber-800/60 px-2 py-0.5 rounded-full">Не подтверждён</span>
              </td>
              <td class="px-4 py-4 w-[160px] min-w-[150px]">
                <!-- Total balance -->
                <div class="whitespace-nowrap">
                  <span class="text-sm font-semibold text-indigo-300">{{ c.loyalty_balance?.toLocaleString('ru-RU') || '0' }}</span>
                  <span class="text-slate-500 text-xs ml-1">pts</span>
                </div>
                <!-- Individual wallets (if multi-wallet) -->
                <div v-if="c.wallets && c.wallets.length > 1" class="flex flex-col gap-1 mt-1.5">
                  <div v-for="w in c.wallets" :key="w.wallet_id || w.id"
                       class="flex items-center justify-between gap-2 text-[11px] px-2 py-0.5 rounded-lg border"
                       :class="w.wallet_type === 1
                         ? 'bg-amber-900/20 border-amber-800/40 text-amber-300'
                         : 'bg-indigo-900/20 border-indigo-800/40 text-indigo-300'">
                    <span class="truncate max-w-[85px] font-medium" :title="w.name">{{ w.name || 'Кошелёк' }}</span>
                    <span class="font-bold whitespace-nowrap">{{ Number(w.balance).toLocaleString('ru-RU') }}</span>
                  </div>
                </div>
              </td>
              <td class="px-4 py-4 w-[150px] min-w-[140px] whitespace-nowrap">
                <span v-if="c.wallet_type === 'google' || (!c.wallet_type && c.google_wallet_object_id)" 
                  class="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg bg-sky-950/40 text-sky-400 border border-sky-800/60 font-medium">
                  <span class="w-4 h-4 rounded-full bg-sky-500/20 flex items-center justify-center text-[10px] font-bold text-sky-300">G</span>
                  Google Wallet
                </span>
                <span v-else-if="c.wallet_type === 'apple'" 
                  class="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg bg-zinc-800/80 text-zinc-200 border border-zinc-700 font-medium">
                  <span class="text-sm leading-none"></span>
                  Apple Wallet
                </span>
                <span v-else 
                  class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-slate-800/60 text-slate-500 border border-slate-700/50">
                  — Не выбрана
                </span>
              </td>
              <td class="px-4 py-4 w-[140px] min-w-[130px] whitespace-nowrap">
                <span v-if="c.onboarding_source === 'web'" 
                  class="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg bg-violet-950/60 text-violet-300 border border-violet-800/80 font-medium">
                  <span class="w-1.5 h-1.5 rounded-full bg-violet-400"></span>
                  🌐 Веб-сайт
                </span>
                <span v-else 
                  class="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg bg-sky-950/60 text-sky-300 border border-sky-800/80 font-medium">
                  <span class="w-1.5 h-1.5 rounded-full bg-sky-400"></span>
                  📱 Telegram
                </span>
              </td>
              <td class="px-4 py-4 w-[170px] min-w-[160px]">
                <span class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full mb-1"
                  :class="c.iiko_customer_id
                    ? 'bg-emerald-900/50 text-emerald-400 border border-emerald-800'
                    : 'bg-slate-800 text-slate-500 border border-slate-700'">
                  {{ c.iiko_customer_id ? '✓ Синхр.' : '— Нет' }}
                </span>
                <div v-if="c.iiko_card_number" class="text-xs text-slate-400 mt-1 font-mono whitespace-nowrap">
                  💳 {{ c.iiko_card_number }}
                </div>
                <div v-if="c.iiko_categories?.length" class="flex flex-wrap gap-1 mt-1">
                  <span v-for="(cat, idx) in c.iiko_categories" :key="idx" class="text-[10px] px-1.5 py-0.5 bg-slate-800 text-slate-400 rounded border border-slate-700">
                    {{ cat.name }}
                  </span>
                </div>
              </td>
              <td class="px-4 py-4 w-[130px] min-w-[120px] whitespace-nowrap">
                <span v-if="c.is_bot_subscribed === true" class="inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full bg-emerald-950/50 text-emerald-400 border border-emerald-800/60">
                  ✓ Подписан
                </span>
                <span v-else-if="c.is_bot_subscribed === false" class="inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full bg-rose-950/50 text-rose-400 border border-rose-900/60">
                  ✗ Отписан
                </span>
                <span v-else class="inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-500 border border-slate-700">
                  — Не решено
                </span>
              </td>
              <td class="px-4 py-4 text-xs text-slate-400 w-[120px] min-w-[110px] whitespace-nowrap">{{ formatDate(c.created_at) }}</td>
              <td class="px-4 py-4 text-center w-[110px] min-w-[100px] whitespace-nowrap">
                <div class="flex items-center justify-center gap-2">
                  <button
                    :id="'btn-sync-' + c.id"
                    @click="syncCustomer(c)"
                    :disabled="syncingId === c.id || pushingId === c.id || !c.phone"
                    :title="c.phone ? 'Обновить данные из iiko' : 'Нет номера телефона'"
                    class="inline-flex items-center justify-center w-9 h-9 rounded-lg transition-all duration-200"
                    :class="syncingId === c.id
                      ? 'bg-indigo-900/40 text-indigo-400 cursor-wait'
                      : c.phone
                        ? 'bg-slate-800 text-slate-400 hover:bg-indigo-900/40 hover:text-indigo-300 border border-slate-700 hover:border-indigo-700'
                        : 'bg-slate-800/50 text-slate-600 cursor-not-allowed border border-slate-700/50'"
                  >
                    <svg
                      class="w-4 h-4 transition-transform duration-300"
                      :class="{ 'animate-spin': syncingId === c.id }"
                      fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
                    >
                      <path stroke-linecap="round" stroke-linejoin="round"
                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                  </button>
                  <button
                    :id="'btn-push-' + c.id"
                    @click="pushCustomer(c)"
                    :disabled="syncingId === c.id || pushingId === c.id || !c.phone"
                    :title="c.phone ? 'Завершить регистрацию (отправить в iiko)' : 'Нет номера телефона'"
                    class="inline-flex items-center justify-center w-9 h-9 rounded-lg transition-all duration-200"
                    :class="pushingId === c.id
                      ? 'bg-emerald-900/40 text-emerald-400 cursor-wait'
                      : c.phone
                        ? 'bg-slate-800 text-slate-400 hover:bg-emerald-900/40 hover:text-emerald-300 border border-slate-700 hover:border-emerald-700'
                        : 'bg-slate-800/50 text-slate-600 cursor-not-allowed border border-slate-700/50'"
                  >
                    <svg
                      v-if="pushingId === c.id"
                      class="w-4 h-4 animate-spin"
                      fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
                    >
                      <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    <svg
                      v-else
                      class="w-4 h-4"
                      fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
                    >
                      <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!customers.length">
              <td colspan="9" class="px-6 py-12 text-center text-slate-500">
                {{ search || selectedWalletFilter ? 'Клиенты не найдены' : 'Нет клиентов' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

        <!-- Pagination -->
        <div v-if="totalCount > 0" class="flex items-center justify-between px-6 py-4 border-t border-slate-800">
          <!-- Page size selector -->
          <div class="flex items-center gap-3">
            <span class="text-xs text-slate-500">Показывать по:</span>
            <div class="flex gap-1">
              <button
                v-for="size in [20, 50]" :key="size"
                @click="changePageSize(size)"
                class="px-3 py-1.5 text-xs font-medium rounded-lg transition-all duration-200"
                :class="pageSize === size
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'bg-slate-800 text-slate-400 hover:text-white border border-slate-700'"
              >
                {{ size }}
              </button>
            </div>
            <span class="text-xs text-slate-500 ml-2">
              Всего: <span class="text-slate-300 font-medium">{{ totalCount }}</span>
            </span>
          </div>

          <!-- Page navigation -->
          <div class="flex items-center gap-1">
            <button
              @click="goToPage(currentPage - 1)"
              :disabled="currentPage <= 1"
              class="px-2.5 py-1.5 text-xs rounded-lg transition-all duration-200"
              :class="currentPage <= 1
                ? 'text-slate-600 cursor-not-allowed'
                : 'text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-700'"
            >
              ←
            </button>
            <template v-for="p in visiblePages" :key="p">
              <span v-if="p === '...'" class="px-2 text-xs text-slate-600">...</span>
              <button
                v-else
                @click="goToPage(p)"
                class="px-3 py-1.5 text-xs font-medium rounded-lg transition-all duration-200"
                :class="p === currentPage
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-700'"
              >
                {{ p }}
              </button>
            </template>
            <button
              @click="goToPage(currentPage + 1)"
              :disabled="currentPage >= totalPages"
              class="px-2.5 py-1.5 text-xs rounded-lg transition-all duration-200"
              :class="currentPage >= totalPages
                ? 'text-slate-600 cursor-not-allowed'
                : 'text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-700'"
            >
              →
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toast = useToastStore()

const customers = ref([])
const loading = ref(true)
const search = ref('')
let searchTimer = null

// Pagination state
const currentPage = ref(1)
const pageSize = ref(20)
const totalCount = ref(0)

const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / pageSize.value)))

const visiblePages = computed(() => {
  const total = totalPages.value
  const current = currentPage.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)

  const pages = []
  pages.push(1)
  if (current > 3) pages.push('...')
  for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) {
    pages.push(i)
  }
  if (current < total - 2) pages.push('...')
  pages.push(total)
  return pages
})

// Sync state
const syncingId = ref(null)
const pushingId = ref(null)
const syncingAll = ref(false)
const pushingAll = ref(false)

// Aggregated database stats from backend
const statsData = ref({
  total_count: 0,
  with_telegram: 0,
  with_phone: 0,
  synced_iiko: 0,
  bot_subscribed: 0,
  google_wallet: 0,
  apple_wallet: 0,
  no_wallet: 0,
})

const stats = computed(() => [
  { label: 'Всего клиентов', value: statsData.value.total_count },
  { label: 'С Telegram ID', value: statsData.value.with_telegram },
  { label: 'С номером телефона', value: statsData.value.with_phone },
  { label: 'Синхр. с iiko', value: statsData.value.synced_iiko },
  { label: 'Подписаны на бота', value: statsData.value.bot_subscribed },
])

// Wallet filter & stats helpers
const selectedWalletFilter = ref('')

function setWalletFilter(type) {
  selectedWalletFilter.value = type
  currentPage.value = 1
  loadCustomers()
}

const totalWithWallet = computed(() => {
  return (statsData.value.google_wallet || 0) + (statsData.value.apple_wallet || 0)
})

const totalWithWalletPercent = computed(() => {
  if (!statsData.value.total_count) return 0
  return Math.round((totalWithWallet.value / statsData.value.total_count) * 100)
})

function walletPercent(val) {
  if (!statsData.value.total_count || !val) return 0
  return Math.round((val / statsData.value.total_count) * 100)
}

function debouncedSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    loadCustomers()
  }, 350)
}

async function loadStats() {
  try {
    const res = await api.get(`/loyalty/organizations/${auth.currentOrgId}/customers/stats/`)
    statsData.value = res.data
  } catch (err) {
    console.error('Failed to load customer stats:', err)
  }
}

async function loadCustomers() {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
    }
    if (search.value.trim()) params.search = search.value.trim()
    if (selectedWalletFilter.value) params.wallet_type = selectedWalletFilter.value
    const res = await api.get(`/loyalty/organizations/${auth.currentOrgId}/customers/`, { params })
    customers.value = res.data.results
    totalCount.value = res.data.count
  } catch {
    toast.error('Не удалось загрузить клиентов')
  } finally {
    loading.value = false
  }
}

function changePageSize(size) {
  pageSize.value = size
  currentPage.value = 1
  loadCustomers()
}

function goToPage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadCustomers()
}

async function syncAllCustomers() {
  if (syncingAll.value || pushingAll.value) return
  syncingAll.value = true
  try {
    const res = await api.post(`/loyalty/organizations/${auth.currentOrgId}/customers/sync-all/`)
    toast.success(res.data.message || 'Синхронизация клиентов с iiko запущена')
    await Promise.all([loadCustomers(), loadStats()])
  } catch (err) {
    const msg = err.response?.data?.error || 'Ошибка при запуске массовой синхронизации'
    toast.error(msg)
  } finally {
    syncingAll.value = false
  }
}

async function pushAllCustomers() {
  if (pushingAll.value || syncingAll.value) return
  pushingAll.value = true
  try {
    const res = await api.post(`/loyalty/organizations/${auth.currentOrgId}/customers/push-all-iiko/`)
    toast.success(res.data.message || 'Выгрузка клиентов в iiko запущена')
    await Promise.all([loadCustomers(), loadStats()])
  } catch (err) {
    const msg = err.response?.data?.error || 'Ошибка при запуске массовой выгрузки'
    toast.error(msg)
  } finally {
    pushingAll.value = false
  }
}

async function syncCustomer(customer) {
  if (syncingId.value || !customer.phone) return
  syncingId.value = customer.id
  try {
    const res = await api.post(`/loyalty/organizations/${auth.currentOrgId}/customers/${customer.id}/sync/`)
    // Update customer in-place in the list
    const idx = customers.value.findIndex(c => c.id === customer.id)
    if (idx !== -1) {
      customers.value[idx] = res.data
    }
    toast.success(`Данные ${customer.first_name || 'клиента'} обновлены из iiko`)
    loadStats()
  } catch (err) {
    const msg = err.response?.data?.error || 'Ошибка синхронизации с iiko'
    toast.error(msg)
  } finally {
    syncingId.value = null
  }
}

async function pushCustomer(customer) {
  if (pushingId.value || syncingId.value || !customer.phone) return
  pushingId.value = customer.id
  try {
    const res = await api.post(`/loyalty/organizations/${auth.currentOrgId}/customers/${customer.id}/push-iiko/`)
    // Update customer in-place in the list
    const idx = customers.value.findIndex(c => c.id === customer.id)
    if (idx !== -1) {
      customers.value[idx] = res.data
    }
    toast.success(`Регистрация ${customer.first_name || 'клиента'} в iiko успешно завершена`)
    loadStats()
  } catch (err) {
    const msg = err.response?.data?.error || 'Ошибка отправки в iiko'
    toast.error(msg)
  } finally {
    pushingId.value = null
  }
}

function exportCSV() {
  if (!customers.value.length) return toast.info('Нет данных для экспорта')
  const headers = ['ID', 'Имя', 'Фамилия', 'Телефон', 'Telegram ID', 'Баллы', 'Тип карты', 'iiko ID', 'Номер карты iiko', 'Рассылка', 'Дата']
  const rows = customers.value.map(c => [
    c.id, c.first_name, c.last_name, c.phone || '', c.telegram_id,
    c.loyalty_balance,
    c.wallet_type === 'google' || (!c.wallet_type && c.google_wallet_object_id) ? 'Google Wallet' : (c.wallet_type === 'apple' ? 'Apple Wallet' : 'Не установлена'),
    c.iiko_customer_id || '', c.iiko_card_number || '',
    c.is_bot_subscribed === true ? 'Подписан' : (c.is_bot_subscribed === false ? 'Отписан' : 'Не решено'),
    c.created_at,
  ])
  const csv = [headers, ...rows].map(r => r.map(v => `"${v}"`).join(',')).join('\n')
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `customers_${auth.currentOrgId}_${new Date().toISOString().slice(0,10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
  toast.success('CSV экспортирован')
}

function initials(c) {
  return ((c.first_name?.[0] || '') + (c.last_name?.[0] || '')).toUpperCase() || '?'
}

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: 'short', year: 'numeric' })
}

onMounted(() => {
  loadCustomers()
  loadStats()
})
</script>
