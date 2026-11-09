(() => {
  if (!("ResizeObserver" in window)) {
    return;
  }

  const sidebar = document.querySelector(".sidebar");
  const navigation = sidebar.querySelector("nav");
  const root = document.documentElement;
  const narrowLayout = window.matchMedia("(max-width: 900px)");

  const updateNavigation = () => {
    const isNarrow = narrowLayout.matches;
    const height = (isNarrow ? sidebar : navigation).getBoundingClientRect().height;
    const fontSize = Number.parseFloat(getComputedStyle(root).fontSize);
    const viewportHeight = window.visualViewport?.height ?? window.innerHeight;
    const fits = isNarrow
      ? height <= viewportHeight * 0.4
      : height + 48 <= viewportHeight;

    sidebar.dataset.sticky = String(fits);
    root.style.setProperty(
      "--sticky-offset",
      isNarrow && fits ? `${Math.ceil(height + fontSize)}px` : "2rem",
    );
  };

  window.addEventListener("resize", updateNavigation);
  window.visualViewport?.addEventListener("resize", updateNavigation);

  new ResizeObserver(updateNavigation).observe(navigation);
  updateNavigation();
})();
