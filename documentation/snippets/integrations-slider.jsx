export const IntegrationsSlider = () => {
  const [position, setPosition] = useState(0)

  const integrations = [
    { type: "image", content: "/integrations/assets/email.png", name: "Email" },
    { type: "image", content: "/integrations/assets/OWM.png", name: "Weather" },
    { type: "image", content: "/integrations/assets/llamacloud-black.svg", name: "LlamaParse" },
    { type: "image", content: "/integrations/assets/FFmpeg-Logo.svg", name: "FFmpeg" },
    { type: "image", content: "/integrations/assets/Cloudinary_logo.svg.png", name: "Cloudinary" },
    { type: "image", content: "/integrations/assets/unstructured-color.png", name: "Unstructured" },
    { type: "image", content: "/integrations/assets/ArXiv_logo_2022.svg.png", name: "Arxiv" },
    { type: "image", content: "/integrations/assets/Algolia_logo_full_blue.svg", name: "Algolia" },
    { type: "image", content: "/integrations/assets/Brave_logo.svg.png", name: "Brave" },
    { type: "image", content: "/integrations/assets/pngimg.com - wikipedia_PNG30.png", name: "Wikipedia" },
    { type: "image", content: "/integrations/assets/logo-full.svg", name: "BrowserBase" },
    { type: "image", content: "/integrations/assets/spider-logo-github-dark.png", name: "Spider" },
    { type: "image", content: "/integrations/assets/Playwright_Logo.svg.png", name: "Remote Browser" },
  ]

  const duplicatedIntegrations = useMemo(
    () => [...integrations, ...integrations],
    []
  )

  useEffect(() => {
    const interval = setInterval(() => {
      setPosition((prev) =>
        prev >= integrations.length * 100 ? 0 : prev + 1
      );
    }, 30);
    return () => clearInterval(interval);
  }, [integrations.length])

  return (
    <div
      style={{
        overflow: "hidden",
        width: "100%",
        padding: "2rem 0",
        background:
          "linear-gradient(to right, rgba(220,220,220,.9), rgba(235,235,235,.95), rgba(220,220,220,.9))",
        borderRadius: "12px",
      }}
    >
      <div
        style={{
          display: "flex",
          transform: `translateX(-${position}px)`,
          transition: position === 0 ? "none" : "transform .1s linear",
        }}
      >
        {duplicatedIntegrations.map((integration, idx) => (
          <div
            key={`${integration.name}-${idx}`}
            style={{
              minWidth: "100px",
              padding: "0 10px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              height: "60px",
            }}
          >
            {integration.type === "emoji" ? (
              <span style={{ fontSize: "3rem" }}>{integration.content}</span>
            ) : (
              <img
                src={integration.content}
                alt={integration.name}
                style={{ maxHeight: "50px", maxWidth: "80px", objectFit: "contain" }}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}