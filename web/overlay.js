(() => {
  const BOT = "https://t.me/smarty_gector_ai_bot?start=vote";
  const pathParts = location.pathname.split("/").filter((part) => part && part !== "index.html");
  const lastPart = pathParts[pathParts.length - 1] || "";
  const rootParts = ["1", "2", "3"].includes(lastPart) ? pathParts.slice(0, -1) : pathParts;
  const ROOT = rootParts.length ? `/${rootParts.join("/")}/` : "/";
  function asset(path) {
    return ROOT + String(path).replace(/^\//, "");
  }
  function pageHref(targetSlug) {
    if (!targetSlug) return ROOT;
    return `${ROOT}${targetSlug}/`;
  }

  const PEOPLE = [
    {
      slug: "1",
      first: "Матвей",
      last: "Петров",
      brand: "М.ПЕТРОВ",
      initials: "МП",
      photo: "assets/petrov.png",
      photoPos: "58% 18%",
      role: "Кандидат",
      lead: "Ознакомительная страница участника. Голос принимается только в Telegram.",
      aboutTitle: "О кандидате",
      about: [
        "Петров Матвей Владимирович.",
        "Здесь будет размещена информация об участнике: портрет, биография и материалы для ознакомления.",
        "После просмотра перейдите в Telegram, чтобы проголосовать.",
      ],
    },
    {
      slug: "2",
      first: "Валентин",
      last: "Пупликов",
      brand: "В.ПУПЛИКОВ",
      initials: "ВП",
      role: "Кандидат",
      lead: "Ознакомительная страница участника. Голос принимается только в Telegram.",
      aboutTitle: "О кандидате",
      about: [
        "Пупликов Валентин Александрович.",
        "Здесь будет размещена информация об участнике: портрет, биография и материалы для ознакомления.",
        "После просмотра перейдите в Telegram, чтобы проголосовать.",
      ],
    },
    {
      slug: "3",
      first: "Дарина",
      last: "Мамедова",
      brand: "Д.МАМЕДОВА",
      initials: "ДМ",
      role: "Кандидат",
      lead: "Ознакомительная страница участника. Голос принимается только в Telegram.",
      aboutTitle: "О кандидате",
      about: [
        "Мамедова Дарина Руслановна.",
        "Здесь будет размещена информация об участнике: портрет, биография и материалы для ознакомления.",
        "После просмотра перейдите в Telegram, чтобы проголосовать.",
      ],
    },
  ];

  const slug =
    typeof window.__PAGE__ === "string"
      ? window.__PAGE__
      : ["1", "2", "3"].includes(lastPart)
        ? lastPart
        : "";
  const person = PEOPLE.find((item) => item.slug === slug) || null;

  function letterBlock(text, extraClass) {
    const wrap = document.createElement("div");
    wrap.className = extraClass;
    const sr = document.createElement("span");
    sr.className = "sr-only";
    sr.textContent = text;
    wrap.appendChild(sr);
    const visible = document.createElement("span");
    visible.setAttribute("aria-hidden", "true");
    visible.className = "inline";
    [...text].forEach((ch) => {
      const outer = document.createElement("span");
      outer.className = "inline-block overflow-hidden align-top";
      const inner = document.createElement("span");
      inner.className = "inline-block will-change-transform";
      inner.textContent = ch === " " ? "\u00a0" : ch;
      outer.appendChild(inner);
      visible.appendChild(outer);
    });
    wrap.appendChild(visible);
    return wrap;
  }

  function findAboutFrame() {
    const about = document.querySelector("#about");
    if (!about) return null;
    return [...about.querySelectorAll("div")].find((node) =>
      (node.className || "").includes("aspect-[4/5]")
    );
  }

  function paintAboutPhoto(target) {
    const frame = findAboutFrame();
    if (!frame) return;
    const box = frame.querySelector(".overflow-hidden") || frame;
    box.style.position = "absolute";
    box.style.inset = "0";
    let img = box.querySelector("img.candidate-photo");
    if (!target.photo) {
      if (img) img.remove();
      return;
    }
    if (!img) {
      img = document.createElement("img");
      img.className = "candidate-photo";
      box.appendChild(img);
    }
    img.src = asset(target.photo);
    img.alt = `${target.first} ${target.last}`;
    img.style.objectPosition = target.photoPos || "center";
    [...box.children].forEach((child) => {
      if (child !== img) child.style.display = "none";
    });
  }

  function paintHeroPhoto(target) {
    const h1 = document.querySelector("#top h1");
    if (!h1) return;
    let wrap = document.getElementById("hero-portrait");
    if (!target.photo) {
      if (wrap) wrap.remove();
      return;
    }
    if (!wrap) {
      wrap = document.createElement("div");
      wrap.id = "hero-portrait";
      h1.parentNode.insertBefore(wrap, h1);
    }
    let img = wrap.querySelector("img");
    if (!img) {
      img = document.createElement("img");
      wrap.appendChild(img);
    }
    img.src = asset(target.photo);
    img.alt = `${target.first} ${target.last}`;
    img.style.objectPosition = target.photoPos || "center";
  }

  function paintHero(target) {
    const h1 = document.querySelector("#top h1");
    if (!h1) return false;
    h1.replaceChildren(
      letterBlock(target.first, "block text-[16vw] md:text-[8.5vw]"),
      letterBlock(target.last, "block text-[16vw] md:text-[8.5vw] italic text-outline")
    );

    const brand = document.querySelector("header a[href='#top'], header a[href='/']");
    if (brand) {
      brand.innerHTML = `${target.brand.split(".")[0]}.<span class="text-gold">${target.brand.split(".").slice(1).join(".")}</span>`;
      brand.setAttribute("href", ROOT);
    }

    placeUmcLogo();
    paintHeroPhoto(target);

    const role = document.querySelector("#top h1 + p, #top .font-display + p");
    const roleNode = [...document.querySelectorAll("#top p")].find((p) => p.textContent.length > 40);
    if (roleNode) roleNode.textContent = target.lead;

    const marquee = [...document.querySelectorAll("#top *")].find((n) =>
      (n.textContent || "").includes("АКТРИСА") && n.children.length === 0
    );
    if (marquee) marquee.textContent = "КАНДИДАТ • ОЗНАКОМЛЕНИЕ • TELEGRAM • ";

    const goldBtn = document.querySelector('#top a[href="#about"]');
    if (goldBtn) {
      goldBtn.textContent = "О участнике";
      goldBtn.setAttribute("href", "#about");
    }
    const videoBtn = document.querySelector('#top a[href*="video"], #top a[href*="olgaspirkina"]');
    if (videoBtn) {
      videoBtn.textContent = "В Telegram";
      videoBtn.setAttribute("href", BOT);
      videoBtn.setAttribute("target", "_blank");
      videoBtn.setAttribute("rel", "noreferrer");
    }

    const contactBtns = document.querySelectorAll('a[href="#contact"]');
    contactBtns.forEach((btn) => {
      btn.textContent = btn.className.includes("uppercase") ? "В Telegram" : "В Telegram";
      btn.setAttribute("href", BOT);
      btn.setAttribute("target", "_blank");
      btn.setAttribute("rel", "noreferrer");
    });

    return true;
  }

  function paintNav() {
    const nav = document.querySelector("header nav");
    if (!nav) return;
    nav.innerHTML = "";
    const home = document.createElement("a");
    home.href = ROOT;
    home.className =
      "group relative text-[13px] uppercase tracking-[0.18em] text-gold hover:text-paper transition-colors";
    home.textContent = "Кандидаты";
    nav.appendChild(home);
    PEOPLE.forEach((item) => {
      const a = document.createElement("a");
      a.href = pageHref(item.slug);
      a.className =
        "group relative text-[13px] uppercase tracking-[0.18em] text-paper-dim hover:text-paper transition-colors";
      a.textContent = item.last;
      if (person && person.slug === item.slug) a.classList.add("text-paper");
      nav.appendChild(a);
    });
    const tg = document.createElement("a");
    tg.href = BOT;
    tg.target = "_blank";
    tg.rel = "noreferrer";
    tg.className =
      "group relative text-[13px] uppercase tracking-[0.18em] text-gold hover:text-paper transition-colors";
    tg.textContent = "Telegram";
    nav.appendChild(tg);
  }

  function paintAbout(target) {
    const about = document.querySelector("#about");
    if (!about) return;
    const h2 = about.querySelector("h2");
    if (h2) h2.textContent = target.aboutTitle;
    const italic = about.querySelector("p.font-display");
    if (italic) italic.textContent = `${target.first} ${target.last}`;
    const paras = [...about.querySelectorAll(".space-y-5 p")];
    target.about.forEach((text, i) => {
      if (paras[i]) paras[i].textContent = text;
    });
    paras.slice(target.about.length).forEach((p) => p.remove());

    const initial = [...about.querySelectorAll("span")].find((s) => s.textContent.trim() === "ОС" || s.textContent.trim().length === 2 && s.className.includes("text-[13rem]"));
    if (initial) initial.textContent = target.initials;

    const quote = about.querySelector("p.font-display.italic.text-lg");
    if (quote) quote.textContent = "«Ознакомьтесь, затем голосуйте в Telegram»";
    const born = [...about.querySelectorAll("p")].find((p) => p.textContent.includes("Родилась") || p.textContent.includes("Кандидат"));
    if (born) born.textContent = target.role;

    about.querySelectorAll("h3, ul").forEach((node) => {
      if (
        node.textContent.includes("Образование") ||
        node.textContent.includes("Статус") ||
        node.textContent.includes("ГИТИС") ||
        node.textContent.includes("Академик")
      ) {
        node.style.display = "none";
      }
    });
    paintAboutPhoto(target);
  }

  function ensureStyle() {
    if (document.getElementById("vote-overlay-css")) return;
    const style = document.createElement("style");
    style.id = "vote-overlay-css";
    style.textContent = `
      #career, #filmography, #awards, #school { display: none !important; }
      #about h3, #about ul { display: none !important; }
      #top p.section-label {
        display: flex !important;
        justify-content: center;
        align-items: center;
        gap: 10px;
        text-transform: none;
        letter-spacing: 0;
        margin-bottom: 1.6rem;
      }
      img.candidate-photo {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        z-index: 3;
        display: block;
      }
      #hero-portrait {
        width: min(210px, 46vw);
        aspect-ratio: 4 / 5;
        margin: 0 auto 1.35rem;
        border-radius: 1.4rem;
        overflow: hidden;
        border: 1px solid rgba(203, 168, 118, 0.35);
        position: relative;
        background: #141210;
      }
      #hero-portrait img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
      }
      #top p.section-label .umc-word {
        height: 84px;
        width: auto;
        object-fit: contain;
        display: block;
        padding: 6px 8px 8px;
        background: #f4efe6;
        border-radius: 10px;
      }
    `;
    document.head.appendChild(style);
  }

  function placeUmcLogo() {
    ensureStyle();
    const kicker = document.querySelector("#top p.section-label");
    if (!kicker || kicker.dataset.umc === "1") return;
    kicker.dataset.umc = "1";
    kicker.replaceChildren();
    const word = document.createElement("img");
    word.className = "umc-word";
    word.src = asset("assets/logo-top2.png");
    word.alt = "УМЦ — Университет мировых цивилизаций";
    kicker.append(word);
  }

  function hideExtra() {
    ensureStyle();
    ["#career", "#filmography", "#awards", "#school"].forEach((sel) => {
      const node = document.querySelector(sel);
      if (node) node.style.setProperty("display", "none", "important");
    });
    const contact = document.querySelector("#contact");
    if (!contact) return;
    const heading = contact.querySelector("h2");
    if (heading) heading.textContent = "Голосование";
    const mail = contact.querySelector('a[href^="mailto"]');
    if (mail) {
      mail.textContent = "Открыть Telegram-бота";
      mail.setAttribute("href", BOT);
    }
  }

  function paintIndex() {
    const h1 = document.querySelector("#top h1");
    if (!h1) return false;
    h1.replaceChildren(
      letterBlock("Трое", "block text-[16vw] md:text-[8.5vw]"),
      letterBlock("кандидатов", "block text-[16vw] md:text-[8.5vw] italic text-outline")
    );
    const brand = document.querySelector("header a[href='#top']");
    if (brand) brand.innerHTML = `В.<span class="text-gold">ЫБОРЫ</span>`;
    placeUmcLogo();
    const roleNode = [...document.querySelectorAll("#top p")].find((p) => p.textContent.length > 40);
    if (roleNode) {
      roleNode.textContent = "Ознакомительная база: лицо и информация на сайте, голос — только в Telegram.";
    }
    const goldBtn = document.querySelector('#top a[href="#about"]');
    if (goldBtn) {
      goldBtn.textContent = "К кандидатам";
      goldBtn.setAttribute("href", pageHref("1"));
    }
    const videoBtn = document.querySelector('#top a[href*="video"], #top a[href*="olgaspirkina"]');
    if (videoBtn) {
      videoBtn.textContent = "В Telegram";
      videoBtn.setAttribute("href", BOT);
      videoBtn.setAttribute("target", "_blank");
    }
    hideExtra();
    const about = document.querySelector("#about");
    if (about) {
      const list = about.querySelector(".space-y-5");
      if (list) {
        list.innerHTML = PEOPLE.map(
          (item) =>
            `<p class="text-paper-dim leading-relaxed text-[15px] md:text-base"><a href="${pageHref(item.slug)}" class="text-gold">${item.first} ${item.last}</a> — открыть страницу участника</p>`
        ).join("");
      }
      const italic = about.querySelector("p.font-display");
      if (italic) italic.textContent = "Выберите участника";
      const h2 = about.querySelector("h2");
      if (h2) h2.textContent = "Участники";
    }
    return true;
  }

  function reveal() {
    document.documentElement.classList.remove("page-boot");
  }

  let applying = false;
  let painted = false;
  function apply() {
    if (applying) return;
    applying = true;
    try {
      paintNav();
      if (!person) {
        if (paintIndex()) hideExtra();
        document.title = "Выборы — ознакомительная база";
        reveal();
        return;
      }
      if (paintHero(person)) {
        paintAbout(person);
        hideExtra();
        document.title = `${person.first} ${person.last} — кандидат`;
        painted = true;
        reveal();
      }
    } finally {
      applying = false;
    }
  }

  const wantedTitle = person ? `${person.first} ${person.last} — кандидат` : "Кандидаты";
  const lockTitle = setInterval(() => {
    if (document.title !== wantedTitle) document.title = wantedTitle;
  }, 200);
  setTimeout(() => clearInterval(lockTitle), 6000);

  const timer = setInterval(() => {
    if (document.querySelector("#top h1")) {
      apply();
      setTimeout(apply, 400);
      setTimeout(apply, 1200);
      clearInterval(timer);
    }
  }, 30);
  setTimeout(() => {
    clearInterval(timer);
    reveal();
  }, 5000);
})();
