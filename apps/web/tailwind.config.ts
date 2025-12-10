import type { Config } from "tailwindcss";

const config: Config = {
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                surface: {
                    950: "var(--surface-950)",
                    900: "var(--surface-900)",
                    800: "var(--surface-800)",
                },
                border: {
                    subtle: "var(--border-subtle)",
                    active: "var(--border-active)",
                },
                terminal: {
                    green: "var(--terminal-green)",
                    red: "var(--terminal-red)",
                    blue: "var(--terminal-blue)",
                },
            },
            backgroundImage: {
                "primary-glow": "var(--primary-glow)",
            },
            fontFamily: {
                sans: ["var(--font-inter)"],
                mono: ["var(--font-mono)"],
            },
        },
    },
    plugins: [],
};
export default config;
