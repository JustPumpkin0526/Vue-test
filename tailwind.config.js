/***************************************************
 * tailwind.config.cjs
 **************************************************/
module.exports = {
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
  plugins: []
};
