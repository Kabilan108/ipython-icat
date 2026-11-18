{
  description = "python devshell with uv";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.nixpkgs-python.url = "github:cachix/nixpkgs-python";

  outputs =
    {
      self,
      nixpkgs,
      nixpkgs-python,
    }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };

      uv = pkgs.stdenvNoCC.mkDerivation rec {
        pname = "uv";
        version = "0.13.9";
        src = pkgs.fetchzip {
          url = "https://github.com/astral-sh/uv/releases/download/${version}/uv-x86_64-unknown-linux-musl.tar.gz";
          hash = "sha256-EnYQLM+lEXCdEvanWzejUaDpLlxBosq32s7HYxKrwTQ=";
        };
        installPhase = ''
          install -Dm755 uv uvx -t $out/bin
        '';
      };

      mkDevShell =
        version:
        pkgs.mkShell {
          buildInputs = [
            nixpkgs-python.packages.${system}."${version}"
            uv
          ];
          shellHook = ''
            export LD_LIBRARY_PATH=${
              pkgs.lib.makeLibraryPath [
                pkgs.zlib
                pkgs.stdenv.cc.cc
              ]
            }:$LD_LIBRARY_PATH
          '';
        };
    in
    {
      devShells.${system} = rec {
        py311 = mkDevShell "3.11.5";
        py312 = mkDevShell "3.12.0";
      };
      devShell.${system} = self.devShells.${system}.py312;
    };
}
