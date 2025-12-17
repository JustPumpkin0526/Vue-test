/***************************************************
 * tailwind.config.cjs
 **************************************************/
module.exports = {
  darkMode: 'class', // class 전략 사용 (html 요소에 dark 클래스 추가)
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts}"
  ],
  theme: {
    extend: {
      transitionProperty: {
        'width': 'width'
      },
      colors: {
        vix: {
          primary: "#2d6cdf",
          ring: "#7aa4ff"
        }
      },
      borderRadius: {
        xl2: "1rem"
      }
    }
  },
  plugins: [require('@tailwindcss/typography')]
};
