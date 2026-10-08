// Filter lists bundled with the extension. "id" is also the ruleset id in
// manifest.json and the file name in rules/ and cosmetic/.
export const LISTS = [
  {
    id: 'easylist',
    name: 'EasyList',
    description: 'Werbung (Banner, Pop-ups, Video-Werbung)',
    url: 'https://easylist.to/easylist/easylist.txt',
    mirrors: ['https://easylist-downloads.adblockplus.org/easylist.txt'],
    defaultEnabled: true,
  },
  {
    id: 'easyprivacy',
    name: 'EasyPrivacy',
    description: 'Tracker, Analyse- und Überwachungsskripte',
    url: 'https://easylist.to/easylist/easyprivacy.txt',
    mirrors: ['https://easylist-downloads.adblockplus.org/easyprivacy.txt'],
    defaultEnabled: true,
  },
  {
    id: 'easylist_germany',
    name: 'EasyList Germany',
    description: 'Werbung auf deutschsprachigen Webseiten',
    url: 'https://easylist.to/easylistgermany/easylistgermany.txt',
    mirrors: ['https://easylist-downloads.adblockplus.org/easylistgermany.txt'],
    defaultEnabled: true,
  },
  {
    id: 'easylist_cookie',
    name: 'Cookie-Hinweise',
    description: 'Blendet Cookie-Banner und Einwilligungs-Dialoge aus',
    url: 'https://secure.fanboy.co.nz/fanboy-cookiemonster.txt',
    mirrors: ['https://easylist-downloads.adblockplus.org/fanboy-cookiemonster.txt'],
    defaultEnabled: false,
  },
  {
    id: 'fanboy_annoyance',
    name: 'Störende Elemente',
    description: 'Newsletter-Pop-ups, Social-Media-Leisten, Chat-Fenster',
    url: 'https://secure.fanboy.co.nz/fanboy-annoyance.txt',
    mirrors: ['https://easylist-downloads.adblockplus.org/fanboy-annoyance.txt'],
    defaultEnabled: false,
  },
];
