<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-indigo-500 selection:text-white relative overflow-x-hidden">
    <!-- Ambient Background Glows -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden z-0">
      <div
        class="absolute -top-32 -left-32 w-96 h-96 rounded-full blur-3xl opacity-20 transition-all duration-700"
        :style="{ backgroundColor: accentColor }"
      ></div>
      <div
        class="absolute top-1/2 -right-32 w-80 h-80 rounded-full blur-3xl opacity-15 transition-all duration-700"
        :style="{ backgroundColor: accentColor }"
      ></div>
    </div>

    <!-- Top Navigation Bar -->
    <header class="relative z-10 w-full max-w-md mx-auto px-4 pt-4 pb-2 flex items-center justify-between">
      <!-- Language Switcher (KZ default) -->
      <div class="inline-flex items-center p-1 bg-slate-900/90 border border-slate-800 rounded-full backdrop-blur-md shadow-lg">
        <button
          type="button"
          @click="lang = 'kz'"
          class="px-3 py-1 rounded-full text-xs font-semibold transition-all duration-200 cursor-pointer"
          :class="lang === 'kz' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'"
        >
          🇰🇿 ҚАЗ
        </button>
        <button
          type="button"
          @click="lang = 'ru'"
          class="px-3 py-1 rounded-full text-xs font-semibold transition-all duration-200 cursor-pointer"
          :class="lang === 'ru' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'"
        >
          🇷🇺 РУС
        </button>
      </div>

      <!-- Telegram Mini App Shortcut (Before and After onboarding) -->
      <a
        v-if="info?.tma_link"
        :href="info.tma_link"
        target="_blank"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 rounded-full text-xs font-semibold transition-all backdrop-blur-md shadow-sm"
      >
        <svg class="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24">
          <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.16.16-.295.295-.605.295l.213-3.053 5.56-5.023c.242-.213-.054-.333-.373-.121l-6.871 4.326-2.962-.924c-.643-.204-.657-.643.136-.953l11.57-4.458c.538-.196 1.006.128.832.943z"/>
        </svg>
        <span>{{ lang === 'kz' ? 'Telegram TMA' : 'Telegram TMA' }}</span>
      </a>
    </header>

    <!-- Main Container (Centered Smartphone Frame on Desktop) -->
    <main class="relative z-10 w-full max-w-md mx-auto flex-1 flex flex-col justify-start px-4 py-2">
      <!-- Loading State -->
      <div v-if="loading" class="flex-1 flex flex-col items-center justify-center py-20 space-y-4">
        <div class="w-10 h-10 border-3 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
        <p class="text-xs text-slate-400 animate-pulse font-medium">
          {{ lang === 'kz' ? 'Жүктелуде...' : 'Загрузка...' }}
        </p>
      </div>

      <!-- Disabled State -->
      <div v-else-if="!info?.is_web_onboarding_enabled" class="flex-1 flex flex-col items-center justify-center text-center p-6 space-y-4">
        <div class="w-16 h-16 rounded-3xl bg-slate-800/80 border border-slate-700 flex items-center justify-center text-3xl">
          🔒
        </div>
        <h2 class="text-lg font-bold text-white">
          {{ lang === 'kz' ? 'Онбординг парақшасы уақытша өшірілген' : 'Страница онбординга временно отключена' }}
        </h2>
        <p class="text-xs text-slate-400 max-w-xs">
          {{ lang === 'kz' ? 'Бұл мекеме онлайн тіркелуді тоқтатты. Сұрақтар бойынша әкімшіге хабарласыңыз.' : 'Ресторан временно приостановил онлайн-регистрацию. Пожалуйста, обратитесь к персоналу.' }}
        </p>
        <a
          v-if="info?.tma_link"
          :href="info.tma_link"
          class="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all inline-flex items-center gap-2"
        >
          <span>💬</span> {{ lang === 'kz' ? 'Telegram арқылы тіркелу' : 'Регистрация через Telegram' }}
        </a>
      </div>

      <!-- Active Onboarding Flow -->
      <div v-else class="space-y-5">
        <!-- Hero Card with Restaurant Banner and Logo -->
        <div class="relative rounded-3xl overflow-hidden border border-slate-800/80 bg-slate-900/60 backdrop-blur-xl shadow-2xl">
          <!-- Banner Image or Gradient Header -->
          <div class="h-36 w-full relative overflow-hidden bg-slate-800">
            <img
              v-if="info.settings?.banner_url"
              :src="info.settings.banner_url"
              alt="Restaurant Banner"
              class="w-full h-full object-cover"
            />
            <div
              v-else
              class="w-full h-full bg-gradient-to-br from-indigo-950 via-slate-900 to-slate-950 flex items-center justify-center"
            >
              <div class="text-center opacity-40">
                <span class="text-4xl block">✨</span>
              </div>
            </div>
            <!-- Gradient Overlay for Contrast -->
            <div class="absolute inset-0 bg-gradient-to-t from-slate-900 via-transparent to-black/20"></div>
          </div>

          <!-- Logo & Header info -->
          <div class="px-5 pb-5 pt-0 relative">
            <div class="flex items-end justify-between -mt-10 mb-3">
              <div class="w-20 h-20 rounded-2xl border-3 border-slate-900 bg-slate-800 overflow-hidden shadow-xl flex items-center justify-center flex-shrink-0">
                <img
                  v-if="info.branding?.logo_url"
                  :src="info.branding.logo_url"
                  alt="Logo"
                  class="w-full h-full object-cover"
                />
                <span v-else class="text-2xl font-black text-indigo-400">
                  {{ (info.organization_name || 'R').charAt(0) }}
                </span>
              </div>

              <!-- Welcome Bonus Badge (if available) -->
              <div
                v-if="bonusText"
                class="px-3 py-1.5 rounded-full text-[11px] font-bold bg-amber-500/15 border border-amber-500/30 text-amber-300 shadow-sm flex items-center gap-1.5"
              >
                <span>🎁</span>
                <span>{{ bonusText }}</span>
              </div>
            </div>

            <h1 class="text-xl font-bold text-white tracking-tight">
              {{ info.organization_name }}
            </h1>
            <p class="text-xs text-indigo-400 font-medium mt-0.5">
              {{ heroTitle }}
            </p>
            <p class="text-xs text-slate-400 mt-1 leading-relaxed">
              {{ heroSubtitle }}
            </p>
          </div>
        </div>

        <!-- NO WHATSAPP NOTIFICATION (Displayed instead of OTP input when number is not registered on WhatsApp) -->
        <div
          v-if="noWhatsappError"
          id="notice-no-whatsapp"
          class="bg-slate-900/80 border border-amber-500/40 rounded-3xl p-6 backdrop-blur-xl shadow-2xl space-y-5 text-center animate-fade-in"
        >
          <div class="w-16 h-16 mx-auto rounded-3xl bg-amber-500/20 text-amber-400 flex items-center justify-center text-3xl border border-amber-500/30 shadow-lg">
            ⚠️
          </div>

          <div class="space-y-2">
            <h3 class="text-base font-bold text-white tracking-tight">
              {{ lang === 'kz' ? 'Бұл нөмірде WhatsApp жоқ!' : 'На данном номере нет WhatsApp!' }}
            </h3>
            <p class="text-xs text-slate-300 leading-relaxed max-w-sm mx-auto">
              {{ lang === 'kz'
                ? `«${formattedPhoneNumber}» нөмірі WhatsApp жүйесінде тіркелмеген. Растау коды тек WhatsApp арқылы жіберіледі. Тіркелу үшін белсенді WhatsApp бар нөмірді енгізіңіз.`
                : `Номер «${formattedPhoneNumber}» не зарегистрирован в WhatsApp. Проверочный код не может быть доставлен. Для регистрации укажите номер с активным WhatsApp.`
              }}
            </p>
          </div>

          <div class="p-3 bg-slate-950/60 border border-slate-800 rounded-2xl flex items-center gap-3 text-left">
            <div class="w-7 h-7 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center text-sm flex-shrink-0">
              💬
            </div>
            <p class="text-[11px] text-slate-400 leading-tight">
              {{ lang === 'kz'
                ? 'Қате енгізілсе, телефон нөмірін тексеріп, қайта жазыңыз.'
                : 'Проверьте правильность ввода или укажите другой номер с WhatsApp.'
              }}
            </p>
          </div>

          <button
            id="btn-change-phone-nowhatsapp"
            type="button"
            @click="changePhoneAfterNoWhatsapp"
            class="w-full py-3.5 px-4 rounded-xl text-xs font-semibold text-white shadow-xl transition-all duration-200 flex items-center justify-center gap-2 cursor-pointer active:scale-98"
            :style="{ backgroundColor: accentColor }"
          >
            ← {{ lang === 'kz' ? 'Басқа телефон нөмірін енгізу' : 'Указать другой номер телефона' }}
          </button>
        </div>

        <!-- STEP 1: Phone input -->
        <div
          v-else-if="step === 'phone'"
          class="bg-slate-900/70 border border-slate-800 rounded-3xl p-5 backdrop-blur-xl shadow-xl space-y-4"
        >
          <div class="space-y-1">
            <h2 class="text-sm font-bold text-white flex items-center gap-2">
              <span class="w-6 h-6 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center text-xs">1</span>
              {{ lang === 'kz' ? 'Телефон нөміріңізді енгізіңіз' : 'Введите ваш номер телефона' }}
            </h2>
            <p class="text-xs text-slate-400 leading-relaxed">
              {{ lang === 'kz' ? 'WhatsApp тіркелген нөмірді көрсетіңіз. Растау коды сол нөмірге жіберіледі.' : 'Укажите номер с активным WhatsApp для получения кода подтверждения.' }}
            </p>
          </div>

          <!-- WhatsApp Notice Callout -->
          <div class="p-3 bg-emerald-950/40 border border-emerald-500/30 rounded-2xl flex items-center gap-3">
            <div class="w-8 h-8 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-base flex-shrink-0">
              💬
            </div>
            <p class="text-[11px] text-emerald-200/90 leading-tight">
              {{ lang === 'kz' ? 'Маңызды: Растау коды тек WhatsApp арқылы жіберіледі' : 'Важно: Код подтверждения отправляется через WhatsApp' }}
            </p>
          </div>

          <!-- Phone Form -->
          <form @submit.prevent="handlePhoneSubmit" class="space-y-4">
            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1.5">
                {{ lang === 'kz' ? 'Телефон нөмірі' : 'Номер телефона' }}
              </label>
              <div class="relative">
                <span class="absolute left-4 top-1/2 -translate-y-1/2 text-sm font-mono text-slate-400 select-none">🇰🇿 +7</span>
                <input
                  id="input-onboarding-phone"
                  v-model="phoneInput"
                  @input="formatPhoneInput"
                  type="tel"
                  placeholder="(701) 000-00-00"
                  maxlength="18"
                  class="w-full bg-slate-950 border border-slate-800 focus:border-indigo-500 text-white font-mono text-base rounded-2xl pl-16 pr-4 py-3.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-all placeholder:text-slate-600"
                  required
                  autofocus
                />
              </div>
            </div>

            <div v-if="errorMessage" class="p-3 bg-rose-950/50 border border-rose-800/60 rounded-xl text-xs text-rose-300 leading-tight">
              {{ errorMessage }}
            </div>

            <button
              id="btn-phone-submit"
              type="submit"
              :disabled="checkingPhone || cleanPhoneDigits.length < 10"
              class="w-full py-3.5 px-4 rounded-2xl text-sm font-semibold text-white shadow-xl transition-all duration-200 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              :style="{ backgroundColor: accentColor }"
            >
              <span v-if="checkingPhone" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              <span v-else>
                {{ lang === 'kz' ? 'Жалғастыру' : 'Продолжить' }} →
              </span>
            </button>
          </form>
        </div>

        <!-- STEP 2: Name & Details input (for NEW guests) -->
        <div
          v-else-if="step === 'details'"
          class="bg-slate-900/70 border border-slate-800 rounded-3xl p-5 backdrop-blur-xl shadow-xl space-y-4"
        >
          <div class="space-y-1">
            <h2 class="text-sm font-bold text-white flex items-center gap-2">
              <span class="w-6 h-6 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center text-xs">2</span>
              {{ lang === 'kz' ? 'Өзіңіз туралы мәліметтер' : 'Данные для выпуска карты' }}
            </h2>
            <p class="text-xs text-slate-400 leading-relaxed">
              {{ lang === 'kz' ? 'Картада көрсетілетін атыңыз бен туған күніңізді енгізіңіз' : 'Укажите имя для карты лояльности и дату рождения для праздничных бонусов' }}
            </p>
          </div>

          <form @submit.prevent="handleDetailsSubmit" class="space-y-3.5">
            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1">
                {{ lang === 'kz' ? 'Атыңыз' : 'Ваше имя' }} <span class="text-rose-400">*</span>
              </label>
              <input
                id="input-first-name"
                v-model="firstName"
                type="text"
                :placeholder="lang === 'kz' ? 'Мысалы: Азамат' : 'Например: Азамат'"
                class="w-full bg-slate-950 border border-slate-800 focus:border-indigo-500 text-white text-sm rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-all placeholder:text-slate-600"
                required
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1">
                {{ lang === 'kz' ? 'Тегіңіз' : 'Фамилия' }} <span class="text-slate-500 text-[11px]">({{ lang === 'kz' ? 'міндетті емес' : 'необязательно' }})</span>
              </label>
              <input
                id="input-last-name"
                v-model="lastName"
                type="text"
                :placeholder="lang === 'kz' ? 'Мысалы: Серіков' : 'Например: Сериков'"
                class="w-full bg-slate-950 border border-slate-800 focus:border-indigo-500 text-white text-sm rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-all placeholder:text-slate-600"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1">
                {{ lang === 'kz' ? 'Туған күніңіз' : 'Дата рождения' }} <span class="text-slate-500 text-[11px]">({{ lang === 'kz' ? 'сыйлықтар үшін' : 'для подарков' }})</span>
              </label>
              <input
                id="input-birthday"
                v-model="birthday"
                type="date"
                class="w-full bg-slate-950 border border-slate-800 focus:border-indigo-500 text-white text-sm rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-all placeholder:text-slate-600"
              />
            </div>

            <div v-if="errorMessage" class="p-3 bg-rose-950/50 border border-rose-800/60 rounded-xl text-xs text-rose-300 leading-tight">
              {{ errorMessage }}
            </div>

            <div class="flex gap-2 pt-2">
              <button
                type="button"
                @click="step = 'phone'"
                class="py-3 px-4 rounded-xl text-xs font-semibold text-slate-400 hover:text-white bg-slate-800/60 hover:bg-slate-800 border border-slate-700 transition-all cursor-pointer"
              >
                ← {{ lang === 'kz' ? 'Артқа' : 'Назад' }}
              </button>

              <button
                id="btn-details-submit"
                type="submit"
                :disabled="sendingOtp || !firstName.trim()"
                class="flex-1 py-3 px-4 rounded-xl text-xs font-semibold text-white shadow-xl transition-all duration-200 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                :style="{ backgroundColor: accentColor }"
              >
                <span v-if="sendingOtp" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                <span v-else>
                  {{ lang === 'kz' ? 'WhatsApp-қа код жіберу' : 'Получить код в WhatsApp' }} →
                </span>
              </button>
            </div>
          </form>
        </div>

        <!-- STEP 3: OTP Verification -->
        <div
          v-else-if="step === 'otp'"
          class="bg-slate-900/70 border border-slate-800 rounded-3xl p-5 backdrop-blur-xl shadow-xl space-y-4"
        >
          <div class="space-y-1">
            <h2 class="text-sm font-bold text-white flex items-center gap-2">
              <span class="w-6 h-6 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center text-xs">3</span>
              {{ lang === 'kz' ? 'Растау кодын енгізіңіз' : 'Введите код подтверждения' }}
            </h2>
            <p class="text-xs text-slate-400 leading-relaxed">
              {{ lang === 'kz' ? 'Біз мына нөмірдегі WhatsApp-қа 4-таңбалы код жібердік:' : 'Мы отправили 4-значный проверочный код в WhatsApp на номер:' }}
              <span class="font-mono text-white font-semibold block mt-0.5">{{ formattedPhoneNumber }}</span>
            </p>
          </div>

          <form @submit.prevent="handleVerifyOtp" class="space-y-4">
            <div>
              <input
                id="input-otp-code"
                v-model="otpCode"
                type="text"
                inputmode="numeric"
                pattern="[0-9]*"
                maxlength="6"
                placeholder="• • • •"
                class="w-full bg-slate-950 border border-slate-800 focus:border-indigo-500 text-white font-mono text-2xl text-center tracking-widest rounded-2xl py-3.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-all placeholder:text-slate-600"
                required
                autofocus
              />
            </div>

            <div v-if="errorMessage" class="p-3 bg-rose-950/50 border border-rose-800/60 rounded-xl text-xs text-rose-300 leading-tight">
              {{ errorMessage }}
            </div>

            <!-- Resend Countdown Timer -->
            <div class="text-center text-xs text-slate-400">
              <span v-if="resendCountdown > 0">
                {{ lang === 'kz' ? `Кодты қайта жіберу: ${resendCountdown} сек` : `Повторная отправка через ${resendCountdown} сек` }}
              </span>
              <button
                v-else
                type="button"
                @click="resendOtp"
                :disabled="sendingOtp"
                class="text-indigo-400 hover:text-indigo-300 font-semibold underline cursor-pointer"
              >
                {{ lang === 'kz' ? 'Кодты қайта жіберу' : 'Отправить код повторно' }}
              </button>
            </div>

            <div class="flex gap-2 pt-2">
              <button
                type="button"
                @click="step = 'details'"
                class="py-3 px-4 rounded-xl text-xs font-semibold text-slate-400 hover:text-white bg-slate-800/60 hover:bg-slate-800 border border-slate-700 transition-all cursor-pointer"
              >
                ← {{ lang === 'kz' ? 'Өзгерту' : 'Изменить' }}
              </button>

              <button
                id="btn-verify-submit"
                type="submit"
                :disabled="verifyingOtp || otpCode.length < 4"
                class="flex-1 py-3 px-4 rounded-xl text-xs font-semibold text-white shadow-xl transition-all duration-200 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                :style="{ backgroundColor: accentColor }"
              >
                <span v-if="verifyingOtp" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                <span v-else>
                  ✓ {{ lang === 'kz' ? 'Тіркелуді аяқтау' : 'Подтвердить и выпустить' }}
                </span>
              </button>
            </div>
          </form>
        </div>

        <!-- STEP 4: SUCCESS & WALLET ADD CARD (No navigation to profile, single OS wallet button) -->
        <div
          v-else-if="step === 'success'"
          class="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 backdrop-blur-xl shadow-2xl space-y-6 animate-fade-in"
        >
          <!-- Celebratory Header -->
          <div class="text-center space-y-2">
            <div class="w-16 h-16 mx-auto rounded-3xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-3xl shadow-lg border border-emerald-500/30">
              🎉
            </div>
            <h2 class="text-xl font-bold text-white tracking-tight">
              {{ isExistingCustomer ? (lang === 'kz' ? 'Қайта оралуыңызбен!' : 'С возвращением!') : (lang === 'kz' ? 'Құттықтаймыз!' : 'Поздравляем!') }}
            </h2>
            <p class="text-xs text-slate-400 max-w-xs mx-auto leading-relaxed">
              {{ isExistingCustomer
                ? (lang === 'kz' ? 'Сіз лоялдық бағдарламасында тіркелгенсіз. Картаңызды смартфон кошелегіне қосыңыз:' : 'Вы уже зарегистрированы в программе лояльности. Добавьте карту в кошелек смартфона:')
                : (lang === 'kz' ? 'Сіздің жеке лоялдық картаңыз сәтті шығарылды. Әрбір тапсырыстан бонустар жинаңыз!' : 'Ваша карта лояльности успешно выпущена. Копите бонусы и получайте привилегии!')
              }}
            </p>
          </div>

          <!-- Interactive 3D Digital Loyalty Card with QR Flip -->
          <div class="card-perspective w-full">
            <div
              id="loyalty-card-flipper"
              class="card-flipper hover:scale-[1.01] active:scale-[0.99] transition-transform duration-200"
              :class="{ 'is-flipped': isCardFlipped }"
              @click="toggleCardFlip"
            >
              <!-- FRONT FACE: Digital Loyalty Card -->
              <div
                class="card-face card-front relative rounded-3xl p-5 text-white overflow-hidden flex flex-col justify-between min-h-[300px] border border-white/20 select-none shadow-2xl"
                :style="cardBackgroundStyle"
              >
                <!-- Background specular glare effects -->
                <div class="absolute -top-20 -left-20 w-52 h-52 rounded-full bg-white/15 blur-2xl pointer-events-none"></div>
                <div class="absolute -bottom-20 -right-20 w-52 h-52 rounded-full bg-black/35 blur-2xl pointer-events-none"></div>
                <div class="absolute inset-0 opacity-[0.03] pointer-events-none bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:16px_16px]"></div>

                <!-- Top Row: Logo, Org Name, Loyalty Badge & Interactive QR Pill -->
                <div class="relative z-10 flex items-center justify-between">
                  <div class="flex items-center gap-2.5 min-w-0 pr-2">
                    <div class="w-8 h-8 rounded-xl bg-white/20 backdrop-blur-md border border-white/30 flex items-center justify-center font-black text-xs text-white shadow-sm flex-shrink-0 overflow-hidden">
                      <img
                        v-if="info?.branding?.logo_url"
                        :src="info.branding.logo_url"
                        alt="Logo"
                        class="w-full h-full object-cover"
                      />
                      <span v-else>{{ (info?.organization_name || 'R').charAt(0) }}</span>
                    </div>
                    <span class="text-xs font-bold tracking-wider uppercase truncate opacity-95">
                      {{ info?.organization_name }}
                    </span>
                  </div>

                  <div class="flex items-center gap-2 flex-shrink-0">
                    <span class="text-[10px] uppercase font-mono px-2 py-0.5 bg-black/35 backdrop-blur-sm rounded-full border border-white/15 text-white/90">
                      Loyalty Pass
                    </span>
                    <button
                      type="button"
                      @click.stop="toggleCardFlip"
                      class="px-2.5 py-1 rounded-full bg-white/25 hover:bg-white/35 active:scale-95 text-white text-[11px] font-semibold flex items-center gap-1 backdrop-blur-md border border-white/30 shadow-sm transition-all cursor-pointer"
                      title="QR-код"
                    >
                      <span class="text-xs">↺</span>
                      <span>QR</span>
                    </button>
                  </div>
                </div>

                <!-- Middle Row: EMV Chip & Contactless Wave Icon -->
                <div class="relative z-10 flex items-center justify-between my-2">
                  <div class="w-11 h-8 rounded-lg bg-gradient-to-br from-amber-300 via-amber-200 to-amber-500 border border-amber-600/40 p-1 flex flex-col justify-between shadow-inner relative overflow-hidden">
                    <div class="absolute inset-0 opacity-40 bg-[linear-gradient(45deg,transparent_40%,rgba(255,255,255,0.8)_50%,transparent_60%)]"></div>
                    <div class="w-full h-[1px] bg-amber-700/40"></div>
                    <div class="flex justify-between items-center px-1">
                      <div class="w-2.5 h-3 border border-amber-700/50 rounded-sm"></div>
                      <div class="w-2.5 h-3 border border-amber-700/50 rounded-sm"></div>
                    </div>
                    <div class="w-full h-[1px] bg-amber-700/40"></div>
                  </div>

                  <div class="text-white/70 flex items-center pr-1">
                    <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                      <path d="M8.5 16.5a5 5 0 0 1 0-9" />
                      <path d="M12 19a8.5 8.5 0 0 0 0-14" />
                      <path d="M15.5 21.5a12 12 0 0 0 0-19" />
                    </svg>
                  </div>
                </div>

                <!-- Bottom Area: Name, Balance, Card Number & Flip Hint -->
                <div class="relative z-10 space-y-2">
                  <div class="flex justify-between items-end">
                    <div>
                      <p class="text-[10px] uppercase text-white/75 font-medium tracking-wider">
                        {{ lang === 'kz' ? 'Карта иесі' : 'Владелец' }}
                      </p>
                      <p class="text-sm font-bold tracking-wide">
                        {{ customerData?.first_name }} {{ customerData?.last_name || '' }}
                      </p>
                    </div>
                    <div class="text-right">
                      <p class="text-[10px] uppercase text-white/75 font-medium tracking-wider">
                        {{ lang === 'kz' ? 'Баланс' : 'Баланс' }}
                      </p>
                      <p class="text-lg font-black font-mono leading-tight">
                        {{ customerData?.balance || 0 }} <span class="text-xs font-normal opacity-80">{{ lang === 'kz' ? 'бонус' : 'баллов' }}</span>
                      </p>
                    </div>
                  </div>

                  <div class="pt-2 border-t border-white/20 flex items-center justify-between text-[11px] font-mono text-white/85">
                    <span>№ {{ customerData?.card_number || '•••• ••••' }}</span>
                    <span>●●●● {{ customerData?.phone ? customerData.phone.slice(-4) : '' }}</span>
                  </div>

                  <!-- Flip Hint Badge -->
                  <div class="pt-1.5 flex items-center justify-center gap-1.5 text-[11px] font-semibold text-white/95">
                    <span class="inline-block animate-spin-slow">↺</span>
                    <span>{{ lang === 'kz' ? 'QR-кодты ашу үшін картаны басыңыз' : 'Нажмите на карту, чтобы открыть QR-код' }}</span>
                  </div>
                </div>
              </div>

              <!-- BACK FACE: High Contrast QR Code for Cashier -->
              <div
                class="card-face card-back absolute inset-0 rounded-3xl p-5 text-white overflow-hidden flex flex-col justify-between min-h-[300px] border border-white/20 select-none shadow-2xl"
                :style="cardBackgroundStyle"
              >
                <!-- Background specular glare effects -->
                <div class="absolute -top-20 -right-20 w-52 h-52 rounded-full bg-white/15 blur-2xl pointer-events-none"></div>
                <div class="absolute -bottom-20 -left-20 w-52 h-52 rounded-full bg-black/35 blur-2xl pointer-events-none"></div>

                <!-- Top Row: Org branding & Flip back button -->
                <div class="relative z-10 flex items-center justify-between">
                  <div class="flex items-center gap-2 min-w-0 pr-2">
                    <div class="w-7 h-7 rounded-lg bg-white/20 backdrop-blur-md border border-white/30 flex items-center justify-center font-black text-xs text-white overflow-hidden">
                      <img
                        v-if="info?.branding?.logo_url"
                        :src="info.branding.logo_url"
                        alt="Logo"
                        class="w-full h-full object-cover"
                      />
                      <span v-else>{{ (info?.organization_name || 'R').charAt(0) }}</span>
                    </div>
                    <span class="text-xs font-bold tracking-wider uppercase truncate opacity-95">
                      {{ info?.organization_name }}
                    </span>
                  </div>

                  <button
                    type="button"
                    @click.stop="toggleCardFlip"
                    class="px-2.5 py-1 rounded-full bg-white/25 hover:bg-white/35 active:scale-95 text-white text-[11px] font-semibold flex items-center gap-1 backdrop-blur-md border border-white/30 shadow-sm transition-all cursor-pointer"
                  >
                    <span>↺</span>
                    <span>{{ lang === 'kz' ? 'Алдыңғы жағы' : 'Лицевая' }}</span>
                  </button>
                </div>

                <!-- Center Area: Crisp White QR Box -->
                <div class="relative z-10 my-auto py-1">
                  <div class="bg-white rounded-2xl p-3 shadow-2xl flex flex-col items-center justify-center mx-auto max-w-[210px] w-full border border-black/10">
                    <div v-if="cardQrCodeDataUrl" class="w-32 h-32 flex items-center justify-center">
                      <img :src="cardQrCodeDataUrl" alt="Card QR Code" class="w-full h-full object-contain" />
                    </div>
                    <div v-else class="w-32 h-32 flex items-center justify-center">
                      <div class="w-8 h-8 border-3 border-slate-300 border-t-slate-800 rounded-full animate-spin"></div>
                    </div>
                    <span class="text-xs font-mono font-bold text-slate-900 tracking-wider mt-1">
                      № {{ customerData?.card_number || customerData?.phone }}
                    </span>
                  </div>
                </div>

                <!-- Bottom Area: Cashier Scan Guidance & Flip Hint -->
                <div class="relative z-10 space-y-1.5 text-center">
                  <p class="text-[11px] text-white/90 leading-tight max-w-xs mx-auto font-medium">
                    {{ lang === 'kz' ? 'Бонустарды жинау немесе есептен шығару үшін QR-кодты кассирге көрсетіңіз' : 'Покажите QR-код кассиру для начисления или списания бонусов' }}
                  </p>
                  <div class="pt-1.5 border-t border-white/20 flex items-center justify-center gap-1.5 text-[10px] font-semibold text-white/80">
                    <span>↺</span>
                    <span>{{ lang === 'kz' ? 'Алдыңғы бетке оралу үшін картаны басыңыз' : 'Нажмите, чтобы вернуться на лицевую сторону' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- WALLET SECTION (Strictly by operating system, no cross-OS buttons) -->
          <div class="space-y-3 pt-2">
            <!-- 1. iOS: ONLY Apple Wallet -->
            <template v-if="deviceOS === 'ios'">
              <button
                v-if="info.is_apple_wallet_enabled"
                id="btn-add-apple-wallet"
                type="button"
                @click="handleAddWallet('apple')"
                :disabled="loadingWallet"
                class="w-full py-4 px-6 rounded-2xl bg-black hover:bg-neutral-900 text-white font-semibold text-sm shadow-xl border border-neutral-700 flex items-center justify-center gap-3 transition-all duration-200 cursor-pointer active:scale-98"
              >
                <span v-if="loadingWallet" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                <template v-else>
                  <span class="text-2xl leading-none"></span>
                  <span>{{ lang === 'kz' ? 'Apple Wallet-ке қосу' : 'Добавить в Apple Wallet' }}</span>
                </template>
              </button>

              <div
                v-else
                id="notice-apple-wallet-disabled"
                class="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 text-center space-y-1.5"
              >
                <div class="w-8 h-8 mx-auto rounded-full bg-neutral-800 border border-neutral-700 flex items-center justify-center text-sm text-neutral-300">
                  
                </div>
                <p class="text-xs font-semibold text-slate-200">
                  {{ lang === 'kz' ? 'Apple Wallet бапталмаған' : 'Apple Wallet не настроен' }}
                </p>
                <p class="text-[11px] text-slate-400 leading-relaxed max-w-xs mx-auto">
                  {{ lang === 'kz'
                    ? 'Бұл мекеме үшін Apple Wallet картасын шығару әлі бапталмаған.'
                    : 'Для данной компании не настроено добавление карты в Apple Wallet.'
                  }}
                </p>
              </div>
            </template>

            <!-- 2. Android: ONLY Google Wallet -->
            <template v-else-if="deviceOS === 'android'">
              <button
                v-if="info.is_google_wallet_enabled"
                id="btn-add-google-wallet"
                type="button"
                @click="handleAddWallet('google')"
                :disabled="loadingWallet"
                class="w-full py-4 px-6 rounded-2xl bg-slate-900 hover:bg-slate-850 text-white font-semibold text-sm shadow-xl border border-slate-700 flex items-center justify-center gap-3 transition-all duration-200 cursor-pointer active:scale-98"
              >
                <span v-if="loadingWallet" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                <template v-else>
                  <span class="w-6 h-6 rounded-lg bg-sky-500/20 text-sky-400 flex items-center justify-center text-xs font-black">G</span>
                  <span>{{ lang === 'kz' ? 'Google Wallet-ке қосу' : 'Добавить в Google Кошелек' }}</span>
                </template>
              </button>

              <div
                v-else
                id="notice-google-wallet-disabled"
                class="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 text-center space-y-1.5"
              >
                <div class="w-8 h-8 mx-auto rounded-full bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-xs font-bold text-sky-400">
                  G
                </div>
                <p class="text-xs font-semibold text-slate-200">
                  {{ lang === 'kz' ? 'Google Кошелек бапталмаған' : 'Google Кошелек не настроен' }}
                </p>
                <p class="text-[11px] text-slate-400 leading-relaxed max-w-xs mx-auto">
                  {{ lang === 'kz'
                    ? 'Бұл мекеме үшін Google Wallet картасын шығару әлі бапталмаған.'
                    : 'Для данной компании не настроено добавление карты в Google Кошелек.'
                  }}
                </p>
              </div>
            </template>

            <!-- 3. Other systems (Desktop Windows, Mac, Linux): No wallet buttons -->
            <template v-else>
              <div
                id="notice-desktop-wallet"
                class="p-3.5 rounded-2xl bg-slate-900/60 border border-slate-800 text-center space-y-1"
              >
                <p class="text-[11px] text-slate-400 leading-relaxed">
                  {{ lang === 'kz'
                    ? 'Картаны телефон кошелегіне (Apple Wallet / Google Wallet) қосу үшін парақшаны смартфоннан ашыңыз.'
                    : 'Для добавления карты в кошелек (Apple Wallet / Google Wallet) откройте эту страницу со смартфона.'
                  }}
                </p>
              </div>
            </template>

            <!-- Notice when wallet added or link opened -->
            <p v-if="walletMessage" class="text-xs text-center text-emerald-400 font-medium">
              ✓ {{ walletMessage }}
            </p>

            <!-- Telegram Mini App link (Always visible after registration) -->
            <div class="pt-3 border-t border-slate-800 text-center space-y-2">
              <p class="text-[11px] text-slate-400">
                {{ lang === 'kz' ? 'Тапсырыс беру және бонустарды көру үшін Telegram-да ашыңыз:' : 'Для заказов и баланса баллов откройте Telegram Mini App:' }}
              </p>
              <a
                v-if="info.tma_link"
                :href="info.tma_link"
                target="_blank"
                class="w-full py-3 px-4 rounded-xl bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 text-xs font-semibold flex items-center justify-center gap-2 transition-all"
              >
                <svg class="w-4 h-4 fill-current" viewBox="0 0 24 24">
                  <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.16.16-.295.295-.605.295l.213-3.053 5.56-5.023c.242-.213-.054-.333-.373-.121l-6.871 4.326-2.962-.924c-.643-.204-.657-.643.136-.953l11.57-4.458c.538-.196 1.006.128.832.943z"/>
                </svg>
                <span>{{ lang === 'kz' ? 'Telegram Mini App-та ашу' : 'Открыть в Telegram Mini App' }}</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Footer -->
    <footer class="relative z-10 w-full max-w-md mx-auto px-4 py-4 text-center text-[11px] text-slate-500 space-y-1">
      <p>© {{ new Date().getFullYear() }} {{ info?.organization_name || 'Loyalty' }}</p>
      <p>
        {{ lang === 'kz' ? 'Әзірлеген' : 'Разработано' }}
        <a
          href="https://loyalty.mevent.kz"
          target="_blank"
          rel="noopener noreferrer"
          class="text-indigo-400 hover:text-indigo-300 font-semibold underline decoration-indigo-400/40 hover:decoration-indigo-300 transition-colors"
        >
          ИП-Maditech
        </a>
      </p>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import QRCode from 'qrcode'

const route = useRoute()
const slug = computed(() => route.params.slug)

// Language state: Kazakh (KZ) default
const lang = ref('kz')

// Step flow: 'phone' -> 'details' -> 'otp' -> 'success'
const step = ref('phone')

const loading = ref(true)
const info = ref(null)
const errorMessage = ref('')
const noWhatsappError = ref(false)

// Form fields
const phoneInput = ref('')
const firstName = ref('')
const lastName = ref('')
const birthday = ref('')
const otpCode = ref('')

// Async states
const checkingPhone = ref(false)
const sendingOtp = ref(false)
const verifyingOtp = ref(false)
const loadingWallet = ref(false)
const walletMessage = ref('')

// Customer result
const isExistingCustomer = ref(false)
const customerData = ref(null)

// 3D Card Flip & QR Code
const isCardFlipped = ref(false)
const cardQrCodeDataUrl = ref('')

function toggleCardFlip() {
  isCardFlipped.value = !isCardFlipped.value
}

async function generateCardQr() {
  const codeValue = customerData.value?.card_number || customerData.value?.phone || ''
  if (!codeValue) return
  try {
    cardQrCodeDataUrl.value = await QRCode.toDataURL(String(codeValue), {
      width: 320,
      margin: 1,
      color: {
        dark: '#0f172a',
        light: '#ffffff',
      },
      errorCorrectionLevel: 'M',
    })
  } catch (err) {
    console.error('Failed to generate card QR code:', err)
  }
}

watch(
  customerData,
  (newVal) => {
    if (newVal) {
      generateCardQr()
    }
  },
  { immediate: true }
)

// Resend timer
const resendCountdown = ref(0)
let timerInterval = null

// Device detection (iOS vs Android vs other)
const deviceOS = computed(() => {
  if (typeof window === 'undefined') return 'other'
  const ua = (navigator.userAgent || navigator.vendor || window.opera || '').toLowerCase()
  const isIOS = /iphone|ipad|ipod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
  if (isIOS) return 'ios'
  if (/android/.test(ua)) return 'android'
  return 'other'
})

// Dynamic branding helpers
const accentColor = computed(() => {
  return info.value?.settings?.accent_color || info.value?.branding?.design_color || '#6366f1'
})

// Premium Card Background Style driven by "Акцентный цвет кнопок и элементов"
const cardBackgroundStyle = computed(() => {
  const color = accentColor.value || '#6366f1'
  return {
    backgroundColor: color,
    backgroundImage: `
      radial-gradient(circle at 12% 15%, rgba(255, 255, 255, 0.28) 0%, transparent 45%),
      radial-gradient(circle at 88% 85%, rgba(0, 0, 0, 0.42) 0%, transparent 55%),
      linear-gradient(135deg, rgba(255, 255, 255, 0.14) 0%, rgba(0, 0, 0, 0.3) 100%)
    `,
    boxShadow: `0 20px 45px -12px rgba(0, 0, 0, 0.6), 0 0 35px -10px ${color}, inset 0 1px 1px 0 rgba(255, 255, 255, 0.45), inset 0 -1px 2px 0 rgba(0, 0, 0, 0.35)`
  }
})

const heroTitle = computed(() => {
  if (lang.value === 'kz') {
    return info.value?.settings?.title_kz || 'Лоялдық картасын алыңыз'
  }
  return info.value?.settings?.title_ru || 'Получите карту лояльности'
})

const heroSubtitle = computed(() => {
  if (lang.value === 'kz') {
    return info.value?.settings?.subtitle_kz || 'Тіркеліп, әрбір тапсырыстан бонустар жинаңыз!'
  }
  return info.value?.settings?.subtitle_ru || 'Зарегистрируйтесь и получайте бонусы с каждого заказа!'
})

const bonusText = computed(() => {
  if (lang.value === 'kz') {
    return info.value?.settings?.welcome_bonus_kz || ''
  }
  return info.value?.settings?.welcome_bonus_ru || ''
})

// Clean digits
const cleanPhoneDigits = computed(() => {
  return phoneInput.value.replace(/\D/g, '')
})

const formattedPhoneNumber = computed(() => {
  const d = cleanPhoneDigits.value
  if (!d) return ''
  return `+7 (${d.slice(0, 3)}) ${d.slice(3, 6)}-${d.slice(6, 8)}-${d.slice(8, 10)}`
})

function formatPhoneInput(event) {
  noWhatsappError.value = false
  errorMessage.value = ''
  let val = event.target.value.replace(/\D/g, '')

  // If 11+ digits entered (e.g. pasted +7... or 8...), strip leading 7/8 country code
  if (val.length > 10 && (val.startsWith('7') || val.startsWith('8'))) {
    val = val.substring(1)
  } else if (val.startsWith('8')) {
    // If user starts typing with 8 (domestic trunk prefix), drop 8 since +7 is already fixed
    val = val.substring(1)
  }
  val = val.substring(0, 10)

  let formatted = ''
  if (val.length > 0) {
    formatted = '(' + val.substring(0, 3)
  }
  if (val.length >= 4) {
    formatted += ') ' + val.substring(3, 6)
  }
  if (val.length >= 7) {
    formatted += '-' + val.substring(6, 8)
  }
  if (val.length >= 9) {
    formatted += '-' + val.substring(8, 10)
  }
  phoneInput.value = formatted
}

function changePhoneAfterNoWhatsapp() {
  noWhatsappError.value = false
  errorMessage.value = ''
  step.value = 'phone'
}

async function loadInfo() {
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await axios.get(`/api/loyalty/public/onboarding/${slug.value}/info/`)
    info.value = res.data
  } catch (e) {
    errorMessage.value = e.response?.data?.error || 'Заведение не найдено'
  } finally {
    loading.value = false
  }
}

// 1. Submit Phone
async function handlePhoneSubmit() {
  errorMessage.value = ''
  noWhatsappError.value = false
  const digits = cleanPhoneDigits.value
  if (digits.length < 10) {
    errorMessage.value = lang.value === 'kz' ? 'Телефон нөмірін толық енгізіңіз' : 'Введите полный номер телефона'
    return
  }

  const fullPhone = `+7${digits}`
  checkingPhone.value = true
  try {
    const res = await axios.post(`/api/loyalty/public/onboarding/${slug.value}/check-phone/`, {
      phone: fullPhone
    })

    if (res.data.exists) {
      // Existing customer: SKIP OTP, go straight to success / wallet screen!
      isExistingCustomer.value = true
      customerData.value = res.data.customer
      step.value = 'success'
    } else {
      // New customer: ask for Name & details first
      isExistingCustomer.value = false
      step.value = 'details'
    }
  } catch (e) {
    errorMessage.value = e.response?.data?.error || (lang.value === 'kz' ? 'Қате орын алды' : 'Произошла ошибка')
  } finally {
    checkingPhone.value = false
  }
}

// 2. Submit Details & Send OTP
async function handleDetailsSubmit() {
  errorMessage.value = ''
  noWhatsappError.value = false
  if (!firstName.value.trim() || firstName.value.trim().length < 2) {
    errorMessage.value = lang.value === 'kz' ? 'Атыңызды дұрыс енгізіңіз (кемінде 2 әріп)' : 'Введите настоящее имя (не менее 2 букв)'
    return
  }

  const fullPhone = `+7${cleanPhoneDigits.value}`
  sendingOtp.value = true
  try {
    await axios.post(`/api/loyalty/public/onboarding/${slug.value}/send-otp/`, {
      phone: fullPhone
    })
    step.value = 'otp'
    startCountdown(60)
  } catch (e) {
    if (e.response?.data?.error_code === 'NO_WHATSAPP') {
      noWhatsappError.value = true
    } else {
      errorMessage.value = e.response?.data?.error || (lang.value === 'kz' ? 'Код жіберу мүмкін болмады' : 'Не удалось отправить код')
    }
  } finally {
    sendingOtp.value = false
  }
}

// Resend OTP
async function resendOtp() {
  if (resendCountdown.value > 0 || sendingOtp.value) return
  errorMessage.value = ''
  noWhatsappError.value = false
  const fullPhone = `+7${cleanPhoneDigits.value}`
  sendingOtp.value = true
  try {
    await axios.post(`/api/loyalty/public/onboarding/${slug.value}/send-otp/`, {
      phone: fullPhone
    })
    startCountdown(60)
  } catch (e) {
    if (e.response?.data?.error_code === 'NO_WHATSAPP') {
      noWhatsappError.value = true
    } else {
      errorMessage.value = e.response?.data?.error || (lang.value === 'kz' ? 'Код жіберу мүмкін болмады' : 'Не удалось отправить код')
    }
  } finally {
    sendingOtp.value = false
  }
}

function startCountdown(sec) {
  resendCountdown.value = sec
  clearInterval(timerInterval)
  timerInterval = setInterval(() => {
    if (resendCountdown.value > 0) {
      resendCountdown.value--
    } else {
      clearInterval(timerInterval)
    }
  }, 1000)
}

// 3. Verify OTP & Create Customer
async function handleVerifyOtp() {
  errorMessage.value = ''
  const fullPhone = `+7${cleanPhoneDigits.value}`
  verifyingOtp.value = true
  try {
    const res = await axios.post(`/api/loyalty/public/onboarding/${slug.value}/verify/`, {
      phone: fullPhone,
      code: otpCode.value.trim(),
      first_name: firstName.value.trim(),
      last_name: lastName.value.trim(),
      birthday: birthday.value || null,
      language: lang.value
    })

    customerData.value = res.data.customer
    isExistingCustomer.value = false
    step.value = 'success'
  } catch (e) {
    errorMessage.value = e.response?.data?.error || (lang.value === 'kz' ? 'Қате растау коды' : 'Неверный код подтверждения')
  } finally {
    verifyingOtp.value = false
  }
}

// 4. Add to Wallet
async function handleAddWallet(walletType) {
  if (!customerData.value?.id) return
  loadingWallet.value = true
  walletMessage.value = ''
  const fullPhone = customerData.value?.phone || `+7${cleanPhoneDigits.value}`
  try {
    const res = await axios.post(`/api/loyalty/public/onboarding/${slug.value}/wallet/`, {
      customer_id: customerData.value.id,
      phone: fullPhone,
      wallet_type: walletType
    })

    if (customerData.value) {
      customerData.value.wallet_type = walletType
    }

    if (walletType === 'google' && res.data.url) {
      window.location.href = res.data.url
    } else if (walletType === 'google') {
      walletMessage.value = lang.value === 'kz' ? 'Google Wallet картасы белгіленді!' : 'Карта Google Wallet успешно выбрана!'
    } else if (walletType === 'apple') {
      walletMessage.value = lang.value === 'kz' ? 'Apple Wallet картасы сәтті қосылды!' : 'Карта Apple Wallet успешно активирована!'
    }
  } catch (e) {
    errorMessage.value = e.response?.data?.error || (lang.value === 'kz' ? 'Кошелекке қосу мүмкін болмады' : 'Не удалось добавить карту в кошелек')
  } finally {
    loadingWallet.value = false
  }
}

onMounted(() => {
  loadInfo()
})

onUnmounted(() => {
  clearInterval(timerInterval)
})
</script>

<style scoped>
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.animate-fade-in {
  animation: fadeIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
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
  z-index: 1;
}

@keyframes spinSlow {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
.animate-spin-slow {
  animation: spinSlow 8s linear infinite;
}
</style>
