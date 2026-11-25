<div align="center">

<img src="docs/banner.jpg" alt="Chân dung + tư thế + trang phục = kết quả" width="900">

<sub>Kết quả là ví dụ do AI tạo, dùng chân dung, tư thế và trang phục từ các thư viện làm tham chiếu. Hình ảnh nguồn thuộc về tác giả của chúng; xem mục Nguồn và giấy phép bên dưới.</sub>

<img src="docs/logo.svg" width="72" alt="PoseWear">

# PoseWear

Nơi tìm ảnh tham chiếu cho vẽ, nhiếp ảnh và tạo ảnh bằng AI.

Mười hai thư viện — tư thế, trang phục, chân dung, biểu cảm và hơn nữa — mỗi thư viện kèm prompt tiếng Trung và tiếng Anh. Chọn tư liệu và tạo ảnh ngay trong trình duyệt, hoặc giao cả bộ cho AI agent của bạn.

[![License: MIT](https://img.shields.io/badge/license-MIT-black)](LICENSE)
[![Cloudflare Pages](https://img.shields.io/badge/Cloudflare-Pages-f38020?logo=cloudflare&logoColor=white)](https://pages.cloudflare.com/)
[![Live demo](https://img.shields.io/badge/demo-posewear.pages.dev-ff2442)](https://posewear.pages.dev)
[![GitHub stars](https://img.shields.io/github/stars/atuizz/posewear?style=flat&color=black)](https://github.com/atuizz/posewear/stargazers)

[Dùng trực tuyến](https://posewear.pages.dev/) · [简体中文](README.md) · [English](README.en.md) · [日本語](README.ja.md) · [Nhật ký thay đổi](CHANGELOG.md)

</div>

> [!CAUTION]
> **Cẩn thận với trang mạo danh**: kênh chính thức duy nhất là [posewear.pages.dev](https://posewear.pages.dev/) và kho này — miễn phí, không cần tài khoản, không có gói trả phí. PoseWear không có ứng dụng Windows hay Android, và không bao giờ phân phối dạng exe/apk qua bất kỳ dịch vụ chia sẻ tệp nào. Các trang như posewear.cn và posewear.art tự xưng là chính thức, cung cấp tải exe/apk hoặc yêu cầu đăng nhập, trả tiền đều là mạo danh — đừng tải xuống, đăng nhập, trả tiền hay nhập API key ở đó.

---

## Tìm tư liệu tham chiếu

- **Tư thế đi theo cặp**: mỗi tư thế có một bản phác thảo và một bản đồ độ sâu từ cùng góc chụp. Lật qua lại giữa chúng trên thẻ, hoặc gửi cả hai vào quá trình tạo ảnh.
- **Không gian làm việc nổi gom tư liệu khi bạn duyệt**: nhấn + trên bất kỳ thẻ nào để thả vào khay ở cuối màn hình. Tạo ảnh ngay từ khay, hoặc sao chép cả bộ — prompt kèm liên kết ảnh công khai.
- **Studio đầy đủ phối hợp tự do**: một nhân vật, một bộ trang phục, các tư thế, cộng thêm biểu cảm, kiểu tóc, bối cảnh, ánh sáng, đạo cụ và nội thất. Dùng nhiều hay ít tùy ý — chỉ một prompt cũng được. Tải ảnh của bạn lên để thử trang phục.
- Mọi thứ bạn tạo được giữ trong Lịch sử, sẵn sàng để xem, tải xuống hoặc xuất dạng ZIP.

![Studio](docs/studio-en.jpg)

<table><tr>
<td width="33%"><img src="docs/home-en.jpg" alt="Trang chủ thư viện"><br><sub>Mười hai thư viện, prompt song ngữ</sub></td>
<td width="33%"><img src="docs/mobile-en.jpg" alt="Duyệt trên điện thoại"><br><sub>Dùng được trên điện thoại nữa</sub></td>
<td><img src="docs/dark-en.jpg" alt="Chế độ tối"><br><sub>Chế độ tối, theo hệ thống của bạn theo mặc định</sub></td>
</tr></table>

Giao diện có tiếng Trung, tiếng Anh, tiếng Nhật và tiếng Việt; mô tả tham chiếu chuyển đổi giữa tiếng Trung và tiếng Anh.

---

## Ba cách tạo ảnh

| Cách | Cách hoạt động |
| --- | --- |
| **API key của riêng bạn** | Dùng key OpenAI, Gemini hoặc Seedream trong studio, hoặc bất kỳ endpoint nào tương thích với giao thức ảnh của OpenAI, Gemini hay xAI. Yêu cầu đi thẳng từ trình duyệt của bạn, hoặc qua proxy của trang (các trạm trung chuyển có thể dùng http/https và mọi cổng). |
| **Mô hình trên máy của bạn** | Nếu bạn chạy ComfyUI hoặc stable-diffusion.cpp, hãy kết nối engine cục bộ và tạo ảnh mà không để hình ảnh rời khỏi máy tính. [Hướng dẫn cài đặt](docs/local-engines.md) |
| **AI agent của bạn** | Kho này kèm một MCP server để agent có thể tìm tư liệu, lấy một góc chụp cụ thể và lắp prompt kèm liên kết ảnh. [Hướng dẫn MCP](mcp/README.md) |

```sh
codex mcp add posewear -- node "$PWD/mcp/server.mjs"
```

Sau đó chỉ cần nói: “Tìm một tư thế ngồi góc nghiêng với trang phục mùa xuân — cho tôi prompt và liên kết ảnh tham chiếu.”

---

## Chạy tại máy của bạn

Yêu cầu Node.js 22.12+:

```sh
git clone https://github.com/atuizz/posewear.git
cd posewear
npm ci
npm start
```

Mở http://127.0.0.1:8787/ . Duyệt, yêu thích và sao chép không cần tài khoản hay key. Danh mục tải từ trang công khai khi mở lần đầu; hình ảnh tải theo yêu cầu.

Mục yêu thích, cài đặt và API key chỉ ở trong trình duyệt của bạn; lịch sử tạo ảnh ở trong cơ sở dữ liệu của trình duyệt. Xóa dữ liệu trang sẽ xóa chúng.

---

## Phát triển

JS thuần, build bằng Python và Cloudflare Pages — không framework. Build, tài sản, kiểm thử và triển khai được ghi trong [AGENTS.md](AGENTS.md); `npm test` chạy bộ hồi quy.

Bản phát hành hiện tại **v1.3.2** (2026-11-24): thông báo mạo danh nay nêu thêm posewear.art; trang chính thức miễn phí, không có tài khoản và không có gói trả phí. [Mọi bản phát hành](CHANGELOG.md)

---

## Nguồn và giấy phép

Mã nguồn, văn bản giao diện và script build là [MIT](LICENSE). Tự host, fork, đóng gói thành client, thậm chí chạy thương mại — tất cả đều được. Một điều kiện: đừng dùng tên PoseWear và đừng mạo danh là dự án chính thức; chỉ cần ghi nguồn. Lưu ý giấy phép hình ảnh tách biệt với giấy phép mã nguồn: một số thư viện thượng nguồn bên dưới không cho phép dùng thương mại hoặc phân phối lại, vì vậy hãy làm rõ quyền với tác giả gốc trước mọi mục đích thương mại, và tự chịu rủi ro. Nguồn hình ảnh:

| Tư liệu | Nguồn |
| --- | --- |
| Tư thế, tư thế độ sâu, trang phục, trang phục anime | ギア / @giaaibusi — hỏi tác giả trước khi dùng thương mại hoặc phân phối lại. [Phác thảo](https://ai-pose-gallery.pages.dev/) · [Độ sâu](https://ai-pose-depth-gallery.pages.dev/) · [Trang phục](https://ai-costume-gallery.pages.dev/) · [Trang phục anime](https://ai-costume-anime-gallery.pages.dev/) |
| Chân dung | Chân dung hư cấu do AI tạo bởi @agi_aibusi, CC0; tác giả đề nghị không đăng lại nguyên trạng hàng loạt. [AI Portrait Gallery](https://ai-portrait-gallery.pages.dev/) |
| Kiểu tóc và một số trang phục anime | たき AI / CharaDB, nhãn CC0, hình ảnh tải từ trang nguồn. [CharaDB](https://charadb-2fi.pages.dev/) |
| Biểu cảm | WaveSpeed AI Emotion Gallery; mô hình đầu ICT FaceKit (© USC Institute for Creative Technologies, MIT) |
| Trang phục lịch sử, bối cảnh, ánh sáng, đạo cụ, nội thất | Shisei / wquguru, CC0 1.0 |

Lấy cảm hứng từ [gen-ai-pose-image](https://github.com/wzc520pyfm/gen-ai-pose-image) và [nvzhuang](https://github.com/paipiange/nvzhuang) — cảm ơn.
