/** @type {import("tailwindcss").Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        tenant: {
          primary: "var(--tenant-primary, #0071CE)",
        },
      },
    },
  },
  plugins: [],
};
