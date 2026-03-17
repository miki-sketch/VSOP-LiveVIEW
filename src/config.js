export const SHEET_ID = '1tiks8xZQukiy-xdzaSUzk-90BoKOv397S47i2HFkggU';

export const GIDS = {
  lives: '0',
  songs: '1268681059',
  reviews: '591211524',
};

export const GAS_URL =
  'https://script.google.com/macros/s/AKfycbyoVXp7Au4e-oDHIm5w-4lo0dAqFWD09-fwMnj--m8pR3lobVdLsFclDy13Lf1TeOLg/exec';

export const csvUrl = (gid) =>
  `https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?tqx=out:csv&gid=${gid}`;
