class Openflow < Formula
  desc "OpenFlow - Open Source Wispr Flow Alternative"
  homepage "https://github.com/sammy4321/OpenFlow"
  url "https://github.com/sammy4321/OpenFlow/archive/refs/tags/v1.0.0.tar.gz"
  version "1.0.0"
  sha256 "REPLACE_WITH_SHA256"

  depends_on "python@3.11"
  depends_on "portaudio" # Required for sounddevice

  def install
    # Install to prefix
    prefix.install Dir["*"]

    # Run the install script within the prefix
    system "bash", "scripts/install.sh"

    # Create a wrapper script that forwards args (e.g. --model large)
    (bin/"openflow").write <<~EOS
      #!/bin/bash
      exec "#{prefix}/venv/bin/python" "#{prefix}/openflow/main.py" "$@"
    EOS
  end

  def caveats
    <<~EOS
      Usage:
        openflow                  # Run with default model (tiny)
        openflow --model large    # Run with a specific model (tiny/base/small/medium/large)

      Models are downloaded automatically on first use.
    EOS
  end
end
