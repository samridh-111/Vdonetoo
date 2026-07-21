export function TopAppBar() {
  return (
    <header className="h-16 flex justify-between items-center px-gutter border-b minimal-divider bg-surface/50 backdrop-blur-md sticky top-0 z-30">
      <div className="flex items-center flex-1">
        <div className="relative w-80">
          <span className="material-symbols-outlined absolute left-0 top-1/2 -translate-y-1/2 text-on-surface-variant/50">
            search
          </span>
        </div>
      </div>
      <div className="flex items-center gap-sm">
        <button className="p-1 text-on-surface-variant hover:text-on-surface transition-colors" type="button">
          <span className="material-symbols-outlined">notifications</span>
        </button>
        <div className="w-7 h-7 rounded-full bg-surface-container-high border minimal-divider flex items-center justify-center overflow-hidden">
          {/* eslint-disable-next-line @next/next/no-img-element -- decorative avatar, same placeholder as the source mockup */}
          <img
            className="w-full h-full object-cover grayscale contrast-125"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuC6zhw1G1npgdSEunBlMmZrVncmvljvzHwDfYenNJzIZgmR2s4UJo44iUPFannDrzP0Xx7Dd9VRkXQ1yPsGoudQpS-PSCI08rzpzMXurvUEC9eMGlhhK-5LcI40XvRQ3xI7AsQrI799nhoKx81rmOkg0mQru9OcVwgcHzatQUsCRlxcOY1kQPkijOsZgwj4-xhZQ9bir77UEDlk6wyMqFeoYW5CEV3MCKXHkuYhS2362iPEGsnCwXLJ"
            alt="User avatar"
          />
        </div>
      </div>
    </header>
  );
}
